import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
数据库加密管理器
确保数据库的库名,表名,列名和内容都被加密存储
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
from typing import Dict, Optional, Any

class DBEncryptionManager:
    """数据库加密管理器"""
    
    def __init__(self, master_key: Optional[str] = None):
        self.master_key = master_key or os.environ.get('DB_ENCRYPTION_KEY', 'MTSCOS_Ai_Project_Master_Key_2024')
        self.fernet = self._init_fernet()
        self.table_name_map = {}
        self.column_name_map = {}
        self._load_mappings()
    
    def _init_fernet(self) -> Fernet:
        """初始化Fernet加密器"""
        password = self.master_key.encode()
        salt = b'MTSCOS_DB_ENCRYPTION_SALT_2024'
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return Fernet(key)
    
    def encrypt_string(self, plaintext: str) -> str:
        """加密字符串"""
        if not plaintext:
            return plaintext
        try:
            return self.fernet.encrypt(plaintext.encode()).decode()
        except Exception as e:
            print(f"加密失败: {e}")
            return plaintext
    
    def decrypt_string(self, ciphertext: str) -> str:
        """解密字符串"""
        if not ciphertext:
            return ciphertext
        try:
            return self.fernet.decrypt(ciphertext.encode()).decode()
        except Exception as e:
            print(f"解密失败: {e}")
            return ciphertext
    
    def encrypt_table_name(self, table_name: str) -> str:
        """加密表名"""
        if table_name in self.table_name_map:
            return self.table_name_map[table_name]
        
        encrypted = hashlib.sha256(f"table_{table_name}".encode()).hexdigest()[:16]
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
        """加密列名"""
        if column_name in self.column_name_map:
            return self.column_name_map[column_name]
        
        encrypted = hashlib.sha256(f"column_{column_name}".encode()).hexdigest()[:12]
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
        return hashlib.sha256(f"db_{db_name}".encode()).hexdigest()[:16]
    
    def encrypt_dict(self, data: Dict) -> Dict:
        """加密字典中的所有字符串值"""
        encrypted = {}
        for key, value in data.items():
            encrypted_key = self.encrypt_column_name(key)
            if isinstance(value, str):
                encrypted[encrypted_key] = self.encrypt_string(value)
            elif isinstance(value, dict):
                encrypted[encrypted_key] = json.dumps(self.encrypt_dict(value))
            elif isinstance(value, list):
                encrypted[encrypted_key] = json.dumps([
                    self.encrypt_string(item) if isinstance(item, str) else item
                    for item in value
                ])
            else:
                encrypted[encrypted_key] = value
        return encrypted
    
    def decrypt_dict(self, data: Dict) -> Dict:
        """解密字典中的所有字符串值"""
        decrypted = {}
        for key, value in data.items():
            decrypted_key = self.decrypt_column_name(key) or key
            if isinstance(value, str):
                decrypted[decrypted_key] = self.decrypt_string(value)
            elif isinstance(value, dict):
                decrypted[decrypted_key] = self.decrypt_dict(value)
            elif isinstance(value, list):
                try:
                    decrypted[decrypted_key] = [
                        self.decrypt_string(item) if isinstance(item, str) else item
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
            with open('db_encryption_mappings.json', 'r') as f:
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
        with open('db_encryption_mappings.json', 'w') as f:
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
        """插入加密数据"""
        encrypted_table_name = self.encrypt_table_name(original_table_name)
        encrypted_data = self.encrypt_dict(data)
        
        columns = ", ".join(encrypted_data.keys())
        placeholders = ", ".join("?" * len(encrypted_data))
        values = list(encrypted_data.values())
        
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO {encrypted_table_name} ({columns}) VALUES ({placeholders})", values)
        conn.commit()
        
        return cursor.lastrowid
    
    def query_encrypted_data(self, conn, original_table_name: str, where_clause: str = "", params: tuple = ()):
        """查询并解密数据"""
        encrypted_table_name = self.encrypt_table_name(original_table_name)
        
        if where_clause:
            sql = f"SELECT * FROM {encrypted_table_name} WHERE {where_clause}"
        else:
            sql = f"SELECT * FROM {encrypted_table_name}"
        
        cursor = conn.cursor()
        cursor.execute(sql, params)
        
        # 获取列名
        column_names = [desc[0] for desc in cursor.description]
        
        # 解密数据
        results = []
        for row in cursor.fetchall():
            row_dict = dict(zip(column_names, row))
            decrypted_row = self.decrypt_dict(row_dict)
            results.append(decrypted_row)
        
        return results
    
    def encrypt_database(self, source_db: str, target_db: str = None):
        """加密整个数据库"""
        if target_db is None:
            target_db = self.encrypt_db_name(source_db) + ".db"
        
        source_conn = sqlite3.connect(source_db)
        target_conn = sqlite3.connect(target_db)
        
        # 获取所有表
        source_cursor = source_conn.cursor()
        source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        
        for table_row in source_cursor.fetchall():
            table_name = table_row[0]
            
            # 获取表结构
            source_cursor.execute(f"PRAGMA table_info({table_name})")
            columns = []
            for col in source_cursor.fetchall():
                col_name = col[1]
                col_type = col[2]
                columns.append((col_name, col_type))
            
            # 创建加密表
            encrypted_cols = {col[0]: col[1] for col in columns}
            self.create_encrypted_table(target_conn, table_name, encrypted_cols)
            
            # 读取并加密数据
            source_cursor.execute(f"SELECT * FROM {table_name}")
            col_names = [desc[0] for desc in source_cursor.description]
            
            for row in source_cursor.fetchall():
                row_dict = dict(zip(col_names, row))
                self.insert_encrypted_data(target_conn, table_name, row_dict)
        
        source_conn.close()
        target_conn.close()
        
        return target_db
    
    def decrypt_database(self, source_db: str, target_db: str):
        """解密整个数据库"""
        source_conn = sqlite3.connect(source_db)
        target_conn = sqlite3.connect(target_db)
        
        source_cursor = source_conn.cursor()
        source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        
        for table_row in source_cursor.fetchall():
            encrypted_table_name = table_row[0]
            original_table_name = self.decrypt_table_name(encrypted_table_name) or encrypted_table_name
            
            source_cursor.execute(f"PRAGMA table_info({encrypted_table_name})")
            columns = []
            for col in source_cursor.fetchall():
                encrypted_col_name = col[1]
                col_type = col[2]
                original_col_name = self.decrypt_column_name(encrypted_col_name) or encrypted_col_name
                columns.append((original_col_name, col_type))
            
            columns_str = ", ".join([f"{col[0]} {col[1]}" for col in columns])
            target_cursor = target_conn.cursor()
            target_cursor.execute(f"CREATE TABLE IF NOT EXISTS {original_table_name} ({columns_str})")
            
            source_cursor.execute(f"SELECT * FROM {encrypted_table_name}")
            col_names = [desc[0] for desc in source_cursor.description]
            
            for row in source_cursor.fetchall():
                row_dict = dict(zip(col_names, row))
                decrypted_row = self.decrypt_dict(row_dict)
                
                insert_cols = ", ".join(decrypted_row.keys())
                placeholders = ", ".join("?" * len(decrypted_row))
                values = list(decrypted_row.values())
                
                target_cursor.execute(f"INSERT INTO {original_table_name} ({insert_cols}) VALUES ({placeholders})", values)
        
        source_conn.close()
        target_conn.commit()
        target_conn.close()
        
        return target_db

# 全局实例
db_encryption_manager = None

def get_db_encryption_manager():
    """获取数据库加密管理器实例"""
    global db_encryption_manager
    if db_encryption_manager is None:
        db_encryption_manager = DBEncryptionManager()
    return db_encryption_manager

if __name__ == "__main__":
    manager = DBEncryptionManager()
    
    print("=== 数据库加密测试 ===")
    
    # 测试加密解密
    test_str = "测试数据"
    encrypted = manager.encrypt_string(test_str)
    decrypted = manager.decrypt_string(encrypted)
    print(f"原文: {test_str}")
    print(f"加密后: {encrypted}")
    print(f"解密后: {decrypted}")
    
    # 测试表名加密
    table_name = "users"
    encrypted_table = manager.encrypt_table_name(table_name)
    print(f"\n表名加密: {table_name} -> {encrypted_table}")
    
    # 测试列名加密
    column_name = "username"
    encrypted_column = manager.encrypt_column_name(column_name)
    print(f"列名加密: {column_name} -> {encrypted_column}")
    
    # 测试字典加密
    test_data = {
        'username': 'testuser',
        'password': 'testpass',
        'email': 'test@example.com'
    }
    encrypted_data = manager.encrypt_dict(test_data)
    decrypted_data = manager.decrypt_dict(encrypted_data)
    print(f"\n字典加密测试:")
    print(f"加密前: {test_data}")
    print(f"加密后: {encrypted_data}")
    print(f"解密后: {decrypted_data}")
    
    logger.info("\n == 测试完成 ===")
