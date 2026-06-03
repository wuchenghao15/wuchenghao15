# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
表名加密工具,用于加密数据库表名,防止黑客撞库攻击
"""

import hashlib
import os
import random
import string
import json
from app.utils.logging import logger
import logging


class TableEncryption:
    """表名加密类"""

    def __init__(self, config_file='app/config/table_mapping.json'):
        """初始化表名加密类

        Args:
            config_file: 表名映射配置文件路径
        """
        self.config_file = config_file
        self.table_mapping = {}
        self.reverse_mapping = {}
        self.secret_key = self._generate_secret_key()
        self.load_mapping()

    def _generate_secret_key(self):
        """生成加密密钥

        Returns:
            str: 加密密钥
        """
        secret_key = os.environ.get('TABLE_ENCRYPTION_KEY')
        if not secret_key:
            secret_key = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
            logger.warning("未找到环境变量 TABLE_ENCRYPTION_KEY,生成随机密钥")
        return secret_key

    def encrypt_table_name(self, table_name):
        """加密表名

        Args:
            table_name: 明文表名

        Returns:
            str: 加密后的表名
        """
        if table_name in self.table_mapping:
            return self.table_mapping[table_name]

        hash_obj = hashlib.sha256(f"{table_name}_{self.secret_key}".encode())
        encrypted_name = f"t_{hash_obj.hexdigest()[:16]}"

        self.table_mapping[table_name] = encrypted_name
        self.reverse_mapping[encrypted_name] = table_name
        self.save_mapping()

        return encrypted_name

    def decrypt_table_name(self, encrypted_name):
        """解密表名

        Args:
            encrypted_name: 加密后的表名

        Returns:
            str: 解密后的表名
        """
        return self.reverse_mapping.get(encrypted_name, encrypted_name)

    def load_mapping(self):
        """加载表名映射"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.table_mapping = data.get('table_mapping', {})
                    self.reverse_mapping = {v: k for k, v in self.table_mapping.items()}
                logger.info(f"表名映射加载成功,共 {len(self.table_mapping)} 个表")
            else:
                os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
                logger.info("表名映射配置文件不存在,将创建新的映射")
        except Exception as e:
            logger.error(f"加载表名映射失败: {str(e)}")
            self.table_mapping = {}
            self.reverse_mapping = {}

    def save_mapping(self):
        """保存表名映射"""
        try:
            data = {
                'table_mapping': self.table_mapping,
                'secret_key_hash': hashlib.md5(self.secret_key.encode()).hexdigest()
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"表名映射保存成功,共 {len(self.table_mapping)} 个表")
        except Exception as e:
            logger.error(f"保存表名映射失败: {str(e)}")

    def get_all_encrypted_tables(self):
        """获取所有加密后的表名

        Returns:
            list: 加密后的表名列表
        """
        return list(self.reverse_mapping.keys())

    def get_all_original_tables(self):
        """获取所有原始表名

        Returns:
            list: 原始表名列表
        """
        return list(self.table_mapping.keys())


table_encryption = TableEncryption()