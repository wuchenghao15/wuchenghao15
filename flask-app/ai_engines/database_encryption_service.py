# -*- coding: utf-8 -*-
"""
MTSCOS 数据库加密服务
提供数据库级、表级、列级和内容级的自动加密功能
支持多种加密策略和密钥管理
"""

import os
import json
import logging
import hashlib
import secrets
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database_encryption_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('database_encryption_service')

class DatabaseEncryptionConfig:
    """数据库加密配置"""
    
    def __init__(self):
        self.encryption_enabled = True
        self.encryption_algorithm = 'AES-256'
        self.encryption_key_length = 256
        self.auto_encrypt_new_tables = True
        self.auto_encrypt_new_columns = True
        self.encryption_key_rotation_days = 30
        
        self.encrypted_databases = []
        self.encrypted_tables = {}
        self.encrypted_columns = {}
        self.sensitive_columns = [
            'password', 'pwd', 'secret', 'token', 'api_key',
            'phone', 'mobile', 'tel', 'email', 'email_address',
            'id_card', 'identity_card', 'ssn', 'passport',
            'address', 'address_detail', 'location',
            'bank_account', 'credit_card', 'card_number',
            'birthday', 'birth_date', 'age',
            'salary', 'income', 'balance', 'amount'
        ]

class ColumnEncryptionSpec:
    """列加密规格"""
    
    def __init__(self, table_name: str, column_name: str, encryption_type: str = 'AES', 
                 key_id: str = None, auto_decrypt: bool = True):
        self.table_name = table_name
        self.column_name = column_name
        self.encryption_type = encryption_type
        self.key_id = key_id or f"key_{table_name}_{column_name}"
        self.auto_decrypt = auto_decrypt
        self.created_at = datetime.now().isoformat()
        self.last_rotated_at = None

class EncryptionKeyManager:
    """加密密钥管理器"""
    
    def __init__(self):
        self.keys = {}
        self.key_versions = {}
        self.master_key = self._generate_master_key()
        logger.info("加密密钥管理器初始化完成")
    
    def _generate_master_key(self) -> str:
        """生成主密钥"""
        return secrets.token_hex(32)
    
    def generate_key(self, key_id: str, password: str = None, salt: str = None) -> str:
        """生成加密密钥"""
        if not salt:
            salt = secrets.token_hex(16)
        
        if password:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt.encode(),
                iterations=480000
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        else:
            key = Fernet.generate_key()
        
        key_str = key.decode() if isinstance(key, bytes) else key
        
        if key_id not in self.key_versions:
            self.key_versions[key_id] = []
        
        version = len(self.key_versions[key_id]) + 1
        
        self.keys[key_id] = {
            'key': key_str,
            'salt': salt,
            'version': version,
            'created_at': datetime.now().isoformat(),
            'active': True
        }
        
        self.key_versions[key_id].append({
            'version': version,
            'key': key_str,
            'created_at': datetime.now().isoformat()
        })
        
        logger.info(f"密钥生成: {key_id} v{version}")
        return key_str
    
    def get_key(self, key_id: str) -> Optional[str]:
        """获取密钥"""
        if key_id in self.keys and self.keys[key_id]['active']:
            return self.keys[key_id]['key']
        return None
    
    def rotate_key(self, key_id: str) -> str:
        """轮换密钥"""
        old_key = self.get_key(key_id)
        if not old_key:
            raise ValueError(f"密钥 {key_id} 不存在")
        
        salt = self.keys[key_id]['salt']
        new_key = self.generate_key(key_id, salt=salt)
        
        self.keys[key_id]['last_rotated_at'] = datetime.now().isoformat()
        
        logger.info(f"密钥轮换完成: {key_id}")
        return new_key
    
    def disable_key(self, key_id: str):
        """禁用密钥"""
        if key_id in self.keys:
            self.keys[key_id]['active'] = False
            logger.info(f"密钥已禁用: {key_id}")

class DataEncryptor:
    """数据加密器"""
    
    def __init__(self, key_manager: EncryptionKeyManager):
        self.key_manager = key_manager
    
    def encrypt(self, data: str, key_id: str) -> str:
        """加密数据"""
        key = self.key_manager.get_key(key_id)
        if not key:
            key = self.key_manager.generate_key(key_id)
        
        try:
            fernet = Fernet(key)
            encrypted = fernet.encrypt(data.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"加密失败: {e}")
            raise
    
    def decrypt(self, encrypted_data: str, key_id: str) -> str:
        """解密数据"""
        key = self.key_manager.get_key(key_id)
        if not key:
            logger.error(f"密钥不存在: {key_id}")
            raise ValueError(f"密钥不存在: {key_id}")
        
        try:
            fernet = Fernet(key)
            decrypted = fernet.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"解密失败: {e}")
            raise
    
    def encrypt_dict(self, data: Dict[str, Any], encrypted_columns: List[str], 
                     table_name: str) -> Dict[str, Any]:
        """加密字典中的指定列"""
        result = data.copy()
        
        for column in encrypted_columns:
            if column in result and result[column]:
                key_id = f"key_{table_name}_{column}"
                result[column] = self.encrypt(str(result[column]), key_id)
        
        return result
    
    def decrypt_dict(self, data: Dict[str, Any], encrypted_columns: List[str], 
                     table_name: str) -> Dict[str, Any]:
        """解密字典中的指定列"""
        result = data.copy()
        
        for column in encrypted_columns:
            if column in result and result[column]:
                try:
                    key_id = f"key_{table_name}_{column}"
                    result[column] = self.decrypt(str(result[column]), key_id)
                except:
                    pass
        
        return result

class DatabaseEncryptionService:
    """数据库加密服务"""
    
    def __init__(self):
        self.config = DatabaseEncryptionConfig()
        self.key_manager = EncryptionKeyManager()
        self.encryptor = DataEncryptor(self.key_manager)
        self.encryption_specs = {}
        logger.info("数据库加密服务初始化完成")
    
    def enable_database_encryption(self, db_name: str):
        """启用数据库加密"""
        if db_name not in self.config.encrypted_databases:
            self.config.encrypted_databases.append(db_name)
            logger.info(f"数据库加密已启用: {db_name}")
    
    def disable_database_encryption(self, db_name: str):
        """禁用数据库加密"""
        if db_name in self.config.encrypted_databases:
            self.config.encrypted_databases.remove(db_name)
            logger.info(f"数据库加密已禁用: {db_name}")
    
    def add_encrypted_table(self, db_name: str, table_name: str):
        """添加加密表"""
        if db_name not in self.config.encrypted_tables:
            self.config.encrypted_tables[db_name] = []
        
        if table_name not in self.config.encrypted_tables[db_name]:
            self.config.encrypted_tables[db_name].append(table_name)
            logger.info(f"表加密已添加: {db_name}.{table_name}")
    
    def add_encrypted_column(self, db_name: str, table_name: str, column_name: str, 
                            encryption_type: str = 'AES'):
        """添加加密列"""
        key_id = f"key_{db_name}_{table_name}_{column_name}"
        
        spec = ColumnEncryptionSpec(table_name, column_name, encryption_type, key_id)
        self.key_manager.generate_key(key_id)
        
        if db_name not in self.config.encrypted_columns:
            self.config.encrypted_columns[db_name] = {}
        
        if table_name not in self.config.encrypted_columns[db_name]:
            self.config.encrypted_columns[db_name][table_name] = []
        
        if column_name not in self.config.encrypted_columns[db_name][table_name]:
            self.config.encrypted_columns[db_name][table_name].append(column_name)
            self.encryption_specs[key_id] = spec
            logger.info(f"列加密已添加: {db_name}.{table_name}.{column_name}")
    
    def encrypt_table_data(self, db_name: str, table_name: str, 
                          rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """加密表数据"""
        encrypted_rows = []
        
        if db_name not in self.config.encrypted_columns:
            return rows
        
        if table_name not in self.config.encrypted_columns[db_name]:
            return rows
        
        encrypted_columns = self.config.encrypted_columns[db_name][table_name]
        
        for row in rows:
            encrypted_row = self.encryptor.encrypt_dict(row, encrypted_columns, f"{db_name}_{table_name}")
            encrypted_rows.append(encrypted_row)
        
        logger.info(f"表数据加密完成: {db_name}.{table_name}, 行数: {len(encrypted_rows)}")
        return encrypted_rows
    
    def decrypt_table_data(self, db_name: str, table_name: str, 
                          rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """解密表数据"""
        decrypted_rows = []
        
        if db_name not in self.config.encrypted_columns:
            return rows
        
        if table_name not in self.config.encrypted_columns[db_name]:
            return rows
        
        encrypted_columns = self.config.encrypted_columns[db_name][table_name]
        
        for row in rows:
            decrypted_row = self.encryptor.decrypt_dict(row, encrypted_columns, f"{db_name}_{table_name}")
            decrypted_rows.append(decrypted_row)
        
        logger.info(f"表数据解密完成: {db_name}.{table_name}, 行数: {len(decrypted_rows)}")
        return decrypted_rows
    
    def encrypt_column_value(self, db_name: str, table_name: str, 
                            column_name: str, value: Any) -> Any:
        """加密单个列值"""
        if not value:
            return value
        
        key_id = f"key_{db_name}_{table_name}_{column_name}"
        
        if key_id not in self.key_manager.keys:
            self.key_manager.generate_key(key_id)
        
        return self.encryptor.encrypt(str(value), key_id)
    
    def decrypt_column_value(self, db_name: str, table_name: str, 
                            column_name: str, value: Any) -> Any:
        """解密单个列值"""
        if not value:
            return value
        
        key_id = f"key_{db_name}_{table_name}_{column_name}"
        
        try:
            return self.encryptor.decrypt(str(value), key_id)
        except:
            return value
    
    def auto_discover_sensitive_columns(self, db_name: str, table_name: str, 
                                      columns: List[str]) -> List[str]:
        """自动发现敏感列"""
        sensitive = []
        
        for col in columns:
            col_lower = col.lower()
            for sensitive_pattern in self.config.sensitive_columns:
                if sensitive_pattern in col_lower:
                    sensitive.append(col)
                    break
        
        return sensitive
    
    def enable_auto_encryption_for_table(self, db_name: str, table_name: str, 
                                        columns: List[str]):
        """为表启用自动加密"""
        self.add_encrypted_table(db_name, table_name)
        
        sensitive_columns = self.auto_discover_sensitive_columns(db_name, table_name, columns)
        
        for col in sensitive_columns:
            self.add_encrypted_column(db_name, table_name, col)
        
        logger.info(f"表自动加密已启用: {db_name}.{table_name}, 加密列: {sensitive_columns}")
        return sensitive_columns
    
    def rotate_all_keys(self):
        """轮换所有密钥"""
        for key_id in list(self.key_manager.keys.keys()):
            if self.key_manager.keys[key_id]['active']:
                self.key_manager.rotate_key(key_id)
        
        logger.info("所有密钥轮换完成")
    
    def export_encryption_config(self) -> Dict[str, Any]:
        """导出加密配置"""
        return {
            'config': {
                'encryption_enabled': self.config.encryption_enabled,
                'encryption_algorithm': self.config.encryption_algorithm,
                'auto_encrypt_new_tables': self.config.auto_encrypt_new_tables,
                'auto_encrypt_new_columns': self.config.auto_encrypt_new_columns,
                'encryption_key_rotation_days': self.config.encryption_key_rotation_days
            },
            'encrypted_databases': self.config.encrypted_databases,
            'encrypted_tables': self.config.encrypted_tables,
            'encrypted_columns': self.config.encrypted_columns,
            'key_info': {
                key_id: {
                    'version': info['version'],
                    'created_at': info['created_at'],
                    'active': info['active']
                }
                for key_id, info in self.key_manager.keys.items()
            },
            'exported_at': datetime.now().isoformat()
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'version': '1.0.0',
            'encryption_enabled': self.config.encryption_enabled,
            'algorithm': self.config.encryption_algorithm,
            'encrypted_databases_count': len(self.config.encrypted_databases),
            'encrypted_tables_count': sum(len(tables) for tables in self.config.encrypted_tables.values()),
            'encrypted_columns_count': sum(
                sum(len(cols) for cols in tables.values()) 
                for tables in self.config.encrypted_columns.values()
            ),
            'keys_count': len(self.key_manager.keys),
            'last_key_rotation': None
        }

database_encryption_service = DatabaseEncryptionService()

if __name__ == '__main__':
    import base64
    
    service = DatabaseEncryptionService()
    
    print("=== 数据库加密服务测试 ===")
    print(json.dumps(service.get_system_status(), indent=2, ensure_ascii=False))
    
    print("\n=== 启用数据库加密 ===")
    service.enable_database_encryption('mtscos_db')
    
    print("\n=== 为表启用自动加密 ===")
    columns = ['id', 'name', 'email', 'phone', 'password', 'address', 'age', 'salary']
    encrypted_cols = service.enable_auto_encryption_for_table('mtscos_db', 'users', columns)
    print(f"自动发现的敏感列: {encrypted_cols}")
    
    print("\n=== 加密表数据 ===")
    user_data = [
        {'id': 1, 'name': '张三', 'email': 'zhangsan@example.com', 'phone': '13812345678', 
         'password': 'secure_password', 'address': '北京市朝阳区', 'age': 25, 'salary': 8000},
        {'id': 2, 'name': '李四', 'email': 'lisi@example.com', 'phone': '13987654321', 
         'password': 'another_password', 'address': '上海市浦东新区', 'age': 30, 'salary': 12000}
    ]
    
    encrypted_data = service.encrypt_table_data('mtscos_db', 'users', user_data)
    print("加密后的数据:")
    for row in encrypted_data:
        print(json.dumps(row, ensure_ascii=False))
    
    print("\n=== 解密表数据 ===")
    decrypted_data = service.decrypt_table_data('mtscos_db', 'users', encrypted_data)
    print("解密后的数据:")
    for row in decrypted_data:
        print(json.dumps(row, ensure_ascii=False))
    
    print("\n=== 验证加密解密 ===")
    all_match = True
    for original, decrypted in zip(user_data, decrypted_data):
        for key in original:
            if str(original[key]) != str(decrypted[key]):
                all_match = False
                break
        if not all_match:
            break
    
    print(f"加密解密验证: {'成功' if all_match else '失败'}")
    
    print("\n=== 加密单个列值 ===")
    encrypted_email = service.encrypt_column_value('mtscos_db', 'users', 'email', 'test@example.com')
    print(f"加密后的邮箱: {encrypted_email[:50]}...")
    
    decrypted_email = service.decrypt_column_value('mtscos_db', 'users', 'email', encrypted_email)
    print(f"解密后的邮箱: {decrypted_email}")
    
    print("\n=== 导出加密配置 ===")
    config = service.export_encryption_config()
    print(json.dumps(config, indent=2, ensure_ascii=False))
    
    print("\n=== 系统状态 ===")
    print(json.dumps(service.get_system_status(), indent=2, ensure_ascii=False))
    
    print("\n=== 测试完成 ===")