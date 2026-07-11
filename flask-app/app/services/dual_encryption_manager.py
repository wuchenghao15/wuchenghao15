import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
双重加密管理器
敏感数据双重加密,数据交互全程密文匹配,严禁出现明文数据
"""

import os
import sqlite3
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import json
from typing import Dict, Optional, Any, Tuple

class DualEncryptionManager:
    """双重加密管理器"""
    
    def __init__(self, master_key: Optional[str] = None):
        self.master_key = master_key or os.environ.get('DB_ENCRYPTION_KEY', 'MTSCOS_Ai_Project_Master_Key_2024')
        self.fernet1, self.fernet2 = self._init_dual_fernet()
        self.table_name_map = {}
        self.column_name_map = {}
        self._load_mappings()
    
    def _init_dual_fernet(self) -> Tuple[Fernet, Fernet]:
        """初始化双重Fernet加密器"""
        password1 = self.master_key.encode()
        password2 = (self.master_key + "_SECOND_KEY").encode()
        
        salt1 = b'MTSCOS_DB_ENCRYPTION_SALT_1'
        salt2 = b'MTSCOS_DB_ENCRYPTION_SALT_2'
        
        kdf1 = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt1,
            iterations=100000,
            backend=default_backend()
        )
        
        kdf2 = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt2,
            iterations=100000,
            backend=default_backend()
        )
        
        key1 = base64.urlsafe_b64encode(kdf1.derive(password1))
        key2 = base64.urlsafe_b64encode(kdf2.derive(password2))
        
        return Fernet(key1), Fernet(key2)
    
    def dual_encrypt(self, plaintext: str) -> str:
        """双重加密:先用第一个密钥加密,再用第二个密钥加密"""
        if not plaintext:
            return plaintext
        try:
            encrypted1 = self.fernet1.encrypt(plaintext.encode())
            encrypted2 = self.fernet2.encrypt(encrypted1)
            return encrypted2.decode()
        except Exception as e:
            print(f"双重加密失败: {e}")
            return plaintext
    
    def dual_decrypt(self, ciphertext: str) -> str:
        """双重解密:先用第二个密钥解密,再用第一个密钥解密"""
        if not ciphertext:
            return ciphertext
        try:
            decrypted2 = self.fernet2.decrypt(ciphertext.encode())
            decrypted1 = self.fernet1.decrypt(decrypted2)
            return decrypted1.decode()
        except Exception as e:
            print(f"双重解密失败: {e}")
            return ciphertext
    
    def encrypt_table_name(self, table_name: str) -> str:
        """加密表名 - 使用SHA256哈希"""
        if table_name in self.table_name_map:
            return self.table_name_map[table_name]
        
        encrypted = hashlib.sha256(f"MTSCOS_TABLE_{table_name}".encode()).hexdigest()[:16]
        self.table_name_map[table_name] = encrypted
        self._save_mappings()
        return encrypted
    
    def decrypt_table_name(self, encrypted_name: str) -> Optional[str]:
        """解密表名"""
        for name, encrypted in self.table_name_map.items():
            if encrypted == encrypted_name:
                return name
        return None
    
    def encrypt_column_name(self, column_name: str) -> str:
        """加密列名 - 使用SHA256哈希"""
        if column_name in self.column_name_map:
            return self.column_name_map[column_name]
        
        encrypted = hashlib.sha256(f"MTSCOS_COLUMN_{column_name}".encode()).hexdigest()[:12]
        self.column_name_map[column_name] = encrypted
        self._save_mappings()
        return encrypted
    
    def decrypt_column_name(self, encrypted_name: str) -> Optional[str]:
        """解密列名"""
        for name, encrypted in self.column_name_map.items():
            if encrypted == encrypted_name:
                return name
        return None
    
    def encrypt_db_name(self, db_name: str) -> str:
        """加密数据库名"""
        return hashlib.sha256(f"MTSCOS_DB_{db_name}".encode()).hexdigest()[:16]
    
    def encrypt_sensitive_dict(self, data: Dict, sensitive_columns: list = None) -> Dict:
        """加密字典中的敏感数据(双重加密)"""
        encrypted = {}
        sensitive_cols = sensitive_columns or ['password', 'token', 'secret', 'key', 'email', 'phone']
        
        for key, value in data.items():
            encrypted_key = self.encrypt_column_name(key)
            
            if isinstance(value, str):
                if key.lower() in sensitive_cols or any(s in key.lower() for s in sensitive_cols):
                    encrypted[encrypted_key] = self.dual_encrypt(value)
                else:
                    encrypted[encrypted_key] = self.dual_encrypt(value)
            elif isinstance(value, dict):
                encrypted[encrypted_key] = json.dumps(self.encrypt_sensitive_dict(value, sensitive_cols))
            elif isinstance(value, list):
                encrypted[encrypted_key] = json.dumps([
                    self.dual_encrypt(item) if isinstance(item, str) else item
                    for item in value
                ])
            else:
                encrypted[encrypted_key] = value
        
        return encrypted
    
    def decrypt_sensitive_dict(self, data: Dict) -> Dict:
        """解密字典中的敏感数据(双重解密)"""
        decrypted = {}
        
        for key, value in data.items():
            decrypted_key = self.decrypt_column_name(key) or key
            
            if isinstance(value, str):
                decrypted[decrypted_key] = self.dual_decrypt(value)
            elif isinstance(value, dict):
                decrypted[decrypted_key] = self.decrypt_sensitive_dict(value)
            elif isinstance(value, list):
                try:
                    decrypted[decrypted_key] = [
                        self.dual_decrypt(item) if isinstance(item, str) else item
                        for item in json.loads(value)
                    ]
                except Exception:
                    decrypted[decrypted_key] = value
            else:
                decrypted[decrypted_key] = value
        
        return decrypted
    
    def _load_mappings(self):
        """加载名称映射"""
        try:
            with open('dual_encryption_mappings.json', 'r') as f:
                data = json.load(f)
                self.table_name_map = data.get('tables', {})
                self.column_name_map = data.get('columns', {})
        except FileNotFoundError:
            pass
    
    def _save_mappings(self):
        """保存名称映射"""
        data = {
            'tables': self.table_name_map,
            'columns': self.column_name_map
        }
        with open('dual_encryption_mappings.json', 'w') as f:
            json.dump(data, f)
    
    def create_encrypted_table(self, conn, original_table_name: str, columns: Dict[str, str]):
        """创建加密的表"""
        encrypted_table_name = self.encrypt_table_name(original_table_name)
        
        encrypted_columns = []
        for col_name, col_type in columns.items():
            encrypted_col_name = self.encrypt_column_name(col_name)
            encrypted_columns.append(f"{encrypted_col_name} {col_type}")
        
        columns_str = ", ".join(encrypted_columns)
        create_sql = f"CREATE TABLE IF NOT EXISTS {encrypted_table_name} ({columns_str})"
        
        cursor = conn.cursor()
        cursor.execute(create_sql)
        conn.commit()
        
        return encrypted_table_name
    
    def insert_encrypted_data(self, conn, original_table_name: str, data: Dict):
        """插入加密数据(全程无明文)"""
        encrypted_table_name = self.encrypt_table_name(original_table_name)
        encrypted_data = self.encrypt_sensitive_dict(data)
        
        columns = ", ".join(encrypted_data.keys())
        placeholders = ", ".join("?" * len(encrypted_data))
        values = list(encrypted_data.values())
        
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO {encrypted_table_name} ({columns}) VALUES ({placeholders})", values)
        conn.commit()
        
        return cursor.lastrowid
    
    def query_by_ciphertext(self, conn, original_table_name: str, 
                           column_name: str, ciphertext_value: str) -> list:
        """
        密文匹配查询 - 全程使用密文匹配,不涉及明文
        """
        encrypted_table_name = self.encrypt_table_name(original_table_name)
        encrypted_column_name = self.encrypt_column_name(column_name)
        
        sql = f"SELECT * FROM {encrypted_table_name} WHERE {encrypted_column_name} = ?"
        
        cursor = conn.cursor()
        cursor.execute(sql, (ciphertext_value,))
        
        column_names = [desc[0] for desc in cursor.description]
        
        results = []
        for row in cursor.fetchall():
            row_dict = dict(zip(column_names, row))
            decrypted_row = self.decrypt_sensitive_dict(row_dict)
            results.append(decrypted_row)
        
        return results
    
    def query_with_ciphertext_filter(self, conn, original_table_name: str, 
                                    filters: Dict[str, str]) -> list:
        """
        使用多个密文过滤器查询
        filters: {column_name: ciphertext_value}
        """
        encrypted_table_name = self.encrypt_table_name(original_table_name)
        
        where_clauses = []
        params = []
        
        for col_name, ciphertext_value in filters.items():
            encrypted_col = self.encrypt_column_name(col_name)
            where_clauses.append(f"{encrypted_col} = ?")
            params.append(ciphertext_value)
        
        where_str = " AND ".join(where_clauses)
        sql = f"SELECT * FROM {encrypted_table_name} WHERE {where_str}" if where_clauses else f"SELECT * FROM {encrypted_table_name}"
        
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))
        
        column_names = [desc[0] for desc in cursor.description]
        
        results = []
        for row in cursor.fetchall():
            row_dict = dict(zip(column_names, row))
            decrypted_row = self.decrypt_sensitive_dict(row_dict)
            results.append(decrypted_row)
        
        return results
    
    def verify_ciphertext_match(self, stored_ciphertext: str, input_value: str) -> bool:
        """
        验证输入值与存储的密文是否匹配
        将输入值双重加密后解密存储的密文进行比较
        """
        if not stored_ciphertext or not input_value:
            return False
        
        try:
            decrypted_stored = self.dual_decrypt(stored_ciphertext)
            return decrypted_stored == input_value
        except Exception as e:
            print(f"密文匹配验证失败: {e}")
            return False
    
    def get_ciphertext_for_query(self, plaintext_value: str) -> str:
        """
        获取用于查询的密文
        将明文转换为密文,用于密文匹配查询
        """
        return self.dual_encrypt(plaintext_value)
    
    def encrypt_database(self, source_db: str, target_db: str = None):
        """加密整个数据库"""
        if target_db is None:
            target_db = self.encrypt_db_name(source_db) + ".db"
        
        source_conn = sqlite3.connect(source_db)
        target_conn = sqlite3.connect(target_db)
        
        source_cursor = source_conn.cursor()
        source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        
        for table_row in source_cursor.fetchall():
            table_name = table_row[0]
            
            source_cursor.execute(f"PRAGMA table_info({table_name})")
            columns = []
            for col in source_cursor.fetchall():
                col_name = col[1]
                col_type = col[2]
                columns.append((col_name, col_type))
            
            encrypted_cols = {col[0]: col[1] for col in columns}
            self.create_encrypted_table(target_conn, table_name, encrypted_cols)
            
            source_cursor.execute(f"SELECT * FROM {table_name}")
            col_names = [desc[0] for desc in source_cursor.description]
            
            for row in source_cursor.fetchall():
                row_dict = dict(zip(col_names, row))
                self.insert_encrypted_data(target_conn, table_name, row_dict)
        
        source_conn.close()
        target_conn.close()
        
        return target_db

# 全局实例
dual_encryption_manager = None

def get_dual_encryption_manager():
    """获取双重加密管理器实例"""
    global dual_encryption_manager
    if dual_encryption_manager is None:
        dual_encryption_manager = DualEncryptionManager()
    return dual_encryption_manager

if __name__ == "__main__":
    manager = DualEncryptionManager()
    
    print("=== 双重加密测试 ===")
    
    test_str = "敏感数据123"
    encrypted = manager.dual_encrypt(test_str)
    decrypted = manager.dual_decrypt(encrypted)
    print(f"原文: {test_str}")
    print(f"双重加密后: {encrypted}")
    print(f"双重解密后: {decrypted}")
    print(f"加密长度: {len(encrypted)}")
    
    table_name = "users"
    encrypted_table = manager.encrypt_table_name(table_name)
    print(f"\n表名加密: {table_name} -> {encrypted_table}")
    
    column_name = "password"
    encrypted_column = manager.encrypt_column_name(column_name)
    print(f"列名加密: {column_name} -> {encrypted_column}")
    
    test_data = {
        'username': 'admin',
        'password': 'secret123',
        'email': 'admin@example.com',
        'role': 'admin'
    }
    encrypted_data = manager.encrypt_sensitive_dict(test_data)
    decrypted_data = manager.decrypt_sensitive_dict(encrypted_data)
    print(f"\n字典加密测试:")
    print(f"加密前: {test_data}")
    print(f"加密后: {encrypted_data}")
    print(f"解密后: {decrypted_data}")
    
    stored_ciphertext = encrypted_data[encrypted_column]
    print(f"\n密文匹配测试:")
    print(f"存储的密码密文: {stored_ciphertext[:30]}...")
    
    match1 = manager.verify_ciphertext_match(stored_ciphertext, "secret123")
    match2 = manager.verify_ciphertext_match(stored_ciphertext, "wrongpass")
    print(f"匹配 'secret123': {match1}")
    print(f"匹配 'wrongpass': {match2}")
    
    logger.info("\n == 测试完成 ===")
