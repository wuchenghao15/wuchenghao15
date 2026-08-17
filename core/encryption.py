# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Encryption Module - 数据加密系统
支持数据库、数据表、数据列级别的加密
"""

from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import hashlib
import uuid
import json
from enum import Enum
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend

class EncryptionLevel(Enum):
    """加密级别"""
    DATABASE = "database"
    TABLE = "table"
    COLUMN = "column"
    NONE = "none"

class EncryptionAlgorithm(Enum):
    """加密算法"""
    AES = "aes"
    RSA = "rsa"
    HASH = "hash"

class EncryptionKey:
    """加密密钥"""
    
    def __init__(self, key_id: str, key_type: str = "aes"):
        self.key_id = key_id
        self.key_type = key_type
        self.created_at = datetime.now()
        self.last_used_at = None
        self.is_active = True
        self.key = None
        self._generate_key()
    
    def _generate_key(self):
        """生成密钥"""
        if self.key_type == "aes":
            self.key = Fernet.generate_key()
        elif self.key_type == "rsa":
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            self.public_key = self.private_key.public_key()
    
    def encrypt(self, data: bytes) -> bytes:
        """加密数据"""
        if self.key_type == "aes":
            f = Fernet(self.key)
            return f.encrypt(data)
        elif self.key_type == "rsa":
            return self.public_key.encrypt(
                data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
        return data
    
    def decrypt(self, encrypted_data: bytes) -> bytes:
        """解密数据"""
        if self.key_type == "aes":
            f = Fernet(self.key)
            return f.decrypt(encrypted_data)
        elif self.key_type == "rsa":
            return self.private_key.decrypt(
                encrypted_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
        return encrypted_data
    
    def get_public_key_pem(self) -> bytes:
        """获取公钥PEM格式"""
        if self.key_type == "rsa":
            return self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        return b""
    
    def get_private_key_pem(self, password: Optional[str] = None) -> bytes:
        """获取私钥PEM格式"""
        if self.key_type == "rsa":
            encryption_algorithm = serialization.NoEncryption()
            if password:
                encryption_algorithm = serialization.BestAvailableEncryption(password.encode())
            
            return self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=encryption_algorithm
            )
        return b""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "key_id": self.key_id,
            "key_type": self.key_type,
            "created_at": self.created_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "is_active": self.is_active
        }


class KeyManager:
    """密钥管理器"""
    
    def __init__(self):
        self.keys: Dict[str, EncryptionKey] = {}
        self.active_key_id = None
        self._init_default_keys()
    
    def _init_default_keys(self):
        """初始化默认密钥"""
        default_key = EncryptionKey("default_aes_key", "aes")
        self.keys[default_key.key_id] = default_key
        self.active_key_id = default_key.key_id
    
    def create_key(self, key_type: str = "aes") -> EncryptionKey:
        """创建新密钥"""
        key_id = f"key_{uuid.uuid4().hex[:8]}"
        key = EncryptionKey(key_id, key_type)
        self.keys[key_id] = key
        return key
    
    def get_key(self, key_id: str) -> Optional[EncryptionKey]:
        """获取密钥"""
        return self.keys.get(key_id)
    
    def get_active_key(self) -> Optional[EncryptionKey]:
        """获取活动密钥"""
        if self.active_key_id:
            return self.keys.get(self.active_key_id)
        return None
    
    def set_active_key(self, key_id: str) -> bool:
        """设置活动密钥"""
        if key_id in self.keys and self.keys[key_id].is_active:
            self.active_key_id = key_id
            return True
        return False
    
    def deactivate_key(self, key_id: str):
        """停用密钥"""
        key = self.keys.get(key_id)
        if key:
            key.is_active = False
    
    def rotate_key(self) -> EncryptionKey:
        """密钥轮换"""
        new_key = self.create_key()
        self.active_key_id = new_key.key_id
        return new_key
    
    def encrypt_data(self, data: Union[str, bytes], key_id: Optional[str] = None) -> bytes:
        """加密数据"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        key = self.get_key(key_id) if key_id else self.get_active_key()
        if key:
            key.last_used_at = datetime.now()
            return key.encrypt(data)
        return data
    
    def decrypt_data(self, encrypted_data: bytes, key_id: Optional[str] = None) -> str:
        """解密数据"""
        key = self.get_key(key_id) if key_id else self.get_active_key()
        if key:
            key.last_used_at = datetime.now()
            return key.decrypt(encrypted_data).decode('utf-8')
        return encrypted_data.decode('utf-8')
    
    def hash_data(self, data: str, salt: Optional[str] = None) -> str:
        """哈希数据"""
        if salt:
            data = f"{salt}{data}"
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    def verify_hash(self, data: str, hash_value: str, salt: Optional[str] = None) -> bool:
        """验证哈希"""
        return self.hash_data(data, salt) == hash_value


class EncryptedColumn:
    """加密列"""
    
    def __init__(self, column_name: str, encrypted: bool = False, 
                 key_id: Optional[str] = None, hash_column: bool = False):
        self.column_name = column_name
        self.encrypted = encrypted
        self.key_id = key_id
        self.hash_column = hash_column
        self.encryption_algorithm = "aes"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "column_name": self.column_name,
            "encrypted": self.encrypted,
            "key_id": self.key_id,
            "hash_column": self.hash_column,
            "encryption_algorithm": self.encryption_algorithm
        }


class EncryptedTable:
    """加密表"""
    
    def __init__(self, table_name: str, encrypted: bool = False, 
                 encryption_level: EncryptionLevel = EncryptionLevel.NONE):
        self.table_name = table_name
        self.encrypted = encrypted
        self.encryption_level = encryption_level
        self.columns: Dict[str, EncryptedColumn] = {}
    
    def add_column(self, column_name: str, encrypted: bool = False, 
                   key_id: Optional[str] = None, hash_column: bool = False):
        """添加加密列"""
        self.columns[column_name] = EncryptedColumn(column_name, encrypted, key_id, hash_column)
    
    def get_column(self, column_name: str) -> Optional[EncryptedColumn]:
        """获取列配置"""
        return self.columns.get(column_name)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "table_name": self.table_name,
            "encrypted": self.encrypted,
            "encryption_level": self.encryption_level.value,
            "columns": {name: col.to_dict() for name, col in self.columns.items()}
        }


class DatabaseEncryptionManager:
    """数据库加密管理器"""
    
    def __init__(self):
        self.key_manager = KeyManager()
        self.tables: Dict[str, EncryptedTable] = {}
        self.encrypted = False
        self.encryption_key_id = None
    
    def enable_encryption(self, key_id: Optional[str] = None):
        """启用数据库加密"""
        self.encrypted = True
        if key_id and key_id in self.key_manager.keys:
            self.encryption_key_id = key_id
        else:
            self.encryption_key_id = self.key_manager.active_key_id
    
    def disable_encryption(self):
        """禁用数据库加密"""
        self.encrypted = False
        self.encryption_key_id = None
    
    def register_table(self, table_name: str, encrypted: bool = False,
                       encryption_level: EncryptionLevel = EncryptionLevel.NONE):
        """注册加密表"""
        self.tables[table_name] = EncryptedTable(table_name, encrypted, encryption_level)
    
    def configure_column(self, table_name: str, column_name: str, 
                         encrypted: bool = False, key_id: Optional[str] = None,
                         hash_column: bool = False):
        """配置列加密"""
        if table_name not in self.tables:
            self.register_table(table_name, False, EncryptionLevel.COLUMN)
        
        self.tables[table_name].add_column(column_name, encrypted, key_id, hash_column)
        
        if encrypted:
            self.tables[table_name].encrypted = True
    
    def encrypt_column_data(self, table_name: str, column_name: str, 
                            data: Union[str, bytes]) -> bytes:
        """加密列数据"""
        if not self.encrypted:
            if isinstance(data, str):
                return data.encode('utf-8')
            return data
        
        table = self.tables.get(table_name)
        if not table:
            if isinstance(data, str):
                return data.encode('utf-8')
            return data
        
        column = table.get_column(column_name)
        if not column or not column.encrypted:
            if isinstance(data, str):
                return data.encode('utf-8')
            return data
        
        if column.hash_column:
            return self.key_manager.hash_data(str(data)).encode('utf-8')
        
        return self.key_manager.encrypt_data(data, column.key_id)
    
    def decrypt_column_data(self, table_name: str, column_name: str, 
                            encrypted_data: bytes) -> str:
        """解密列数据"""
        if not self.encrypted:
            return encrypted_data.decode('utf-8')
        
        table = self.tables.get(table_name)
        if not table:
            return encrypted_data.decode('utf-8')
        
        column = table.get_column(column_name)
        if not column or not column.encrypted:
            return encrypted_data.decode('utf-8')
        
        if column.hash_column:
            return encrypted_data.decode('utf-8')
        
        return self.key_manager.decrypt_data(encrypted_data, column.key_id)
    
    def encrypt_table_data(self, table_name: str, row_data: Dict[str, Any]) -> Dict[str, Any]:
        """加密整行数据"""
        encrypted_row = {}
        
        for column_name, value in row_data.items():
            if value is None:
                encrypted_row[column_name] = None
                continue
            
            encrypted_value = self.encrypt_column_data(table_name, column_name, str(value))
            encrypted_row[column_name] = encrypted_value
        
        return encrypted_row
    
    def decrypt_table_data(self, table_name: str, encrypted_row: Dict[str, Any]) -> Dict[str, Any]:
        """解密整行数据"""
        decrypted_row = {}
        
        for column_name, value in encrypted_row.items():
            if value is None:
                decrypted_row[column_name] = None
                continue
            
            if isinstance(value, bytes):
                decrypted_value = self.decrypt_column_data(table_name, column_name, value)
            else:
                decrypted_value = value
            
            try:
                decrypted_value = int(decrypted_value)
            except ValueError:
                try:
                    decrypted_value = float(decrypted_value)
                except ValueError:
                    pass
            
            decrypted_row[column_name] = decrypted_value
        
        return decrypted_row
    
    def get_table_config(self, table_name: str) -> Optional[Dict[str, Any]]:
        """获取表加密配置"""
        table = self.tables.get(table_name)
        if table:
            return table.to_dict()
        return None
    
    def get_all_tables_config(self) -> Dict[str, Any]:
        """获取所有表加密配置"""
        return {name: table.to_dict() for name, table in self.tables.items()}
    
    def generate_encryption_key(self, key_type: str = "aes") -> str:
        """生成加密密钥"""
        key = self.key_manager.create_key(key_type)
        return key.key_id
    
    def rotate_keys(self) -> str:
        """轮换密钥"""
        new_key = self.key_manager.rotate_key()
        return new_key.key_id
    
    def export_keys(self, file_path: str, password: Optional[str] = None):
        """导出密钥"""
        keys_data = []
        for key_id, key in self.key_manager.keys.items():
            key_info = key.to_dict()
            if key.key_type == "rsa":
                key_info["public_key"] = key.get_public_key_pem().decode('utf-8')
                key_info["private_key"] = key.get_private_key_pem(password).decode('utf-8')
            keys_data.append(key_info)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(keys_data, f, ensure_ascii=False, indent=2)
    
    def import_keys(self, file_path: str, password: Optional[str] = None):
        """导入密钥"""
        with open(file_path, 'r', encoding='utf-8') as f:
            keys_data = json.load(f)
        
        for key_info in keys_data:
            key = EncryptionKey(key_info["key_id"], key_info["key_type"])
            key.created_at = datetime.fromisoformat(key_info["created_at"])
            key.last_used_at = datetime.fromisoformat(key_info["last_used_at"]) if key_info["last_used_at"] else None
            key.is_active = key_info["is_active"]
            
            if key.key_type == "rsa" and "private_key" in key_info:
                key.private_key = serialization.load_pem_private_key(
                    key_info["private_key"].encode('utf-8'),
                    password=password.encode() if password else None,
                    backend=default_backend()
                )
                key.public_key = key.private_key.public_key()
            
            self.key_manager.keys[key.key_id] = key


# 全局实例
encryption_manager = DatabaseEncryptionManager()

# 预设常见表的加密配置
def setup_default_encryption():
    """设置默认加密配置"""
    tables = [
        {"name": "users", "columns": [
            {"name": "password", "encrypted": True, "hash_column": True},
            {"name": "email", "encrypted": True},
            {"name": "phone", "encrypted": True}
        ]},
        {"name": "students", "columns": [
            {"name": "password", "encrypted": True, "hash_column": True},
            {"name": "email", "encrypted": True},
            {"name": "phone", "encrypted": True},
            {"name": "address", "encrypted": True}
        ]},
        {"name": "teachers", "columns": [
            {"name": "password", "encrypted": True, "hash_column": True},
            {"name": "email", "encrypted": True},
            {"name": "phone", "encrypted": True}
        ]},
        {"name": "session_logs", "columns": [
            {"name": "user_agent", "encrypted": True},
            {"name": "ip_address", "encrypted": True}
        ]},
        {"name": "exam_papers", "columns": [
            {"name": "content", "encrypted": True}
        ]}
    ]
    
    for table in tables:
        encryption_manager.register_table(table["name"], False, EncryptionLevel.COLUMN)
        for column in table["columns"]:
            encryption_manager.configure_column(
                table["name"],
                column["name"],
                column.get("encrypted", False),
                key_id=None,
                hash_column=column.get("hash_column", False)
            )

setup_default_encryption()
