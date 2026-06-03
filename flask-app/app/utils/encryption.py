# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
数据加密工具,用于加密和解密敏感数据
"""

import logging
logger = logging.getLogger(__name__)
import base64
import hashlib
import json
from cryptography.fernet import Fernet
import os
from datetime import datetime

class EncryptionManager:
    """数据加密管理器 - 单例模式"""

    _instance = None

    def __new__(cls):
        """单例模式"""
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化加密管理器"""
        encryption_key = os.environ.get('DATABASE_ENCRYPTION_KEY', None)
        if not encryption_key:
            encryption_key = 'MTSCOS_AI_Project_Database_Encryption_Key_2026'
            
        key_hash = hashlib.sha256(encryption_key.encode()).digest()
        self.fernet_key = base64.urlsafe_b64encode(key_hash)
        self.cipher = Fernet(self.fernet_key)

    def encrypt(self, data):
        """加密数据"""
        try:
            if data is None:
                return None
            
            if isinstance(data, (dict, list)):
                data_str = json.dumps(data)
            else:
                data_str = str(data)

            encrypted_data = self.cipher.encrypt(data_str.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            print(f"加密数据失败: {str(e)}")
            return data

    def decrypt(self, encrypted_data):
        """解密数据"""
        try:
            if encrypted_data is None:
                return None
            
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            decrypted_str = decrypted_bytes.decode()

            try:
                return json.loads(decrypted_str)
            except json.JSONDecodeError:
                return decrypted_str
        except Exception as e:
            print(f"解密数据失败: {str(e)}")
            return encrypted_data

    def generate_key(self):
        """生成新的加密密钥"""
        return Fernet.generate_key().decode()

encryption_manager = EncryptionManager()