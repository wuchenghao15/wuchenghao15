#!/usr/bin/env python3
"""
表名加密工具，用于加密数据库表名，防止黑客撞库攻击
"""

import hashlib
import json
import os
import random
import string
from app.utils.logging import logger

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
        # 从环境变量获取密钥，否则生成一个随机密钥
        secret_key = os.environ.get('TABLE_ENCRYPTION_KEY')
        if not secret_key:
            secret_key = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
            logger.warning("未找到环境变量 TABLE_ENCRYPTION_KEY，生成随机密钥")
        return secret_key
    
    def encrypt_table_name(self, table_name):
        """加密表名
        
        Args:
            table_name: 明文表名
            
        Returns:
            str: 加密后的表名
        """
        # 如果表名已经在映射中，直接返回加密后的表名
        if table_name in self.table_mapping:
            return self.table_mapping[table_name]
        
        # 生成加密表名
        # 使用SHA256加密，取前16位，并添加前缀
        hash_obj = hashlib.sha256(f"{table_name}_{self.secret_key}".encode())
        encrypted_name = f"t_{hash_obj.hexdigest()[:16]}"
        
        # 添加到映射
        self.table_mapping[table_name] = encrypted_name
        self.reverse_mapping[encrypted_name] = table_name
        
        # 保存映射
        self.save_mapping()
        
        return encrypted_name
    
    def decrypt_table_name(self, encrypted_name):
        """解密表名
        
        Args:
            encrypted_name: 加密后的表名
            
        Returns:
            str: 明文表名
        """
        return self.reverse_mapping.get(encrypted_name, encrypted_name)
    
    def load_mapping(self):
        """加载表名映射"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.table_mapping = data.get('table_mapping', {})
                    # 生成反向映射
                    self.reverse_mapping = {v: k for k, v in self.table_mapping.items()}
                logger.info(f"表名映射加载成功，共 {len(self.table_mapping)} 个表")
            else:
                # 创建配置目录
                os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
                logger.info("表名映射配置文件不存在，将创建新的映射")
        except Exception as e:
            logger.error(f"加载表名映射失败: {str(e)}")
            self.table_mapping = {}
            self.reverse_mapping = {}
    
    def save_mapping(self):
        """保存表名映射"""
        try:
            data = {
                'table_mapping': self.table_mapping
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"表名映射保存成功，共 {len(self.table_mapping)} 个表")
        except Exception as e:
            logger.error(f"保存表名映射失败: {str(e)}")
    
    def encrypt_sql(self, sql):
        """加密SQL语句中的表名
        
        Args:
            sql: SQL语句
            
        Returns:
            str: 加密后的SQL语句
        """
        # 分割SQL语句
        tokens = sql.split()
        encrypted_tokens = []
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            # 检查是否是需要加密的表名
            if i > 0:
                prev_token = tokens[i-1].upper()
                
                # 处理 SELECT FROM 语句
                if prev_token == 'FROM':
                    # 去除可能的引号
                    table_name = token.strip('`'"'"'')
                    # 检查是否已经是加密表名
                    if not table_name.startswith('t_') or len(table_name) != 18:
                        # 加密表名
                        encrypted_name = self.encrypt_table_name(table_name)
                        # 保留原始的引号
                        if token.startswith('`') and token.endswith('`'):
                            encrypted_tokens.append(f"`{encrypted_name}`")
                        elif token.startswith("'") and token.endswith("'"):
                            encrypted_tokens.append(f"'{encrypted_name}'")
                        elif token.startswith('"') and token.endswith('"'):
                            encrypted_tokens.append(f'"{encrypted_name}"')
                        else:
                            encrypted_tokens.append(encrypted_name)
                    else:
                        # 已经是加密表名，直接添加
                        encrypted_tokens.append(token)
                # 处理 INSERT INTO 语句
                elif prev_token == 'INTO':
                    # 去除可能的引号
                    table_name = token.strip('`'"'"'')
                    # 检查是否已经是加密表名
                    if not table_name.startswith('t_') or len(table_name) != 18:
                        # 加密表名
                        encrypted_name = self.encrypt_table_name(table_name)
                        # 保留原始的引号
                        if token.startswith('`') and token.endswith('`'):
                            encrypted_tokens.append(f"`{encrypted_name}`")
                        elif token.startswith("'") and token.endswith("'"):
                            encrypted_tokens.append(f"'{encrypted_name}'")
                        elif token.startswith('"') and token.endswith('"'):
                            encrypted_tokens.append(f'"{encrypted_name}"')
                        else:
                            encrypted_tokens.append(encrypted_name)
                    else:
                        # 已经是加密表名，直接添加
                        encrypted_tokens.append(token)
                # 处理 UPDATE 语句
                elif prev_token == 'UPDATE':
                    # 去除可能的引号
                    table_name = token.strip('`'"'"'')
                    # 检查是否已经是加密表名
                    if not table_name.startswith('t_') or len(table_name) != 18:
                        # 加密表名
                        encrypted_name = self.encrypt_table_name(table_name)
                        # 保留原始的引号
                        if token.startswith('`') and token.endswith('`'):
                            encrypted_tokens.append(f"`{encrypted_name}`")
                        elif token.startswith("'") and token.endswith("'"):
                            encrypted_tokens.append(f"'{encrypted_name}'")
                        elif token.startswith('"') and token.endswith('"'):
                            encrypted_tokens.append(f'"{encrypted_name}"')
                        else:
                            encrypted_tokens.append(encrypted_name)
                    else:
                        # 已经是加密表名，直接添加
                        encrypted_tokens.append(token)
                # 处理 JOIN 语句
                elif prev_token == 'JOIN':
                    # 加密表名
                    table_name = token.strip('`'"'"'')
                    # 检查是否已经是加密表名
                    if not table_name.startswith('t_') or len(table_name) != 18:
                        # 加密表名
                        encrypted_name = self.encrypt_table_name(table_name)
                        # 保留原始的引号
                        if token.startswith('`') and token.endswith('`'):
                            encrypted_tokens.append(f"`{encrypted_name}`")
                        elif token.startswith("'") and token.endswith("'"):
                            encrypted_tokens.append(f"'{encrypted_name}'")
                        elif token.startswith('"') and token.endswith('"'):
                            encrypted_tokens.append(f'"{encrypted_name}"')
                        else:
                            encrypted_tokens.append(encrypted_name)
                    else:
                        # 已经是加密表名，直接添加
                        encrypted_tokens.append(token)
                # 处理 CREATE TABLE IF NOT EXISTS 语句
                elif prev_token == 'EXISTS':
                    # 检查是否是 CREATE TABLE IF NOT EXISTS 语句
                    if i > 4 and tokens[i-5].upper() == 'CREATE' and tokens[i-4].upper() == 'TABLE' and tokens[i-3].upper() == 'IF' and tokens[i-2].upper() == 'NOT':
                        # 加密表名
                        table_name = token.strip('`'"'"'')
                        # 检查是否已经是加密表名
                        if not table_name.startswith('t_') or len(table_name) != 18:
                            # 加密表名
                            encrypted_name = self.encrypt_table_name(table_name)
                            # 保留原始的引号
                            if token.startswith('`') and token.endswith('`'):
                                encrypted_tokens.append(f"`{encrypted_name}`")
                            elif token.startswith("'") and token.endswith("'"):
                                encrypted_tokens.append(f"'{encrypted_name}'")
                            elif token.startswith('"') and token.endswith('"'):
                                encrypted_tokens.append(f'"{encrypted_name}"')
                            else:
                                encrypted_tokens.append(encrypted_name)
                        else:
                            # 已经是加密表名，直接添加
                            encrypted_tokens.append(token)
                    else:
                        # 直接添加 token
                        encrypted_tokens.append(token)
                # 处理 TABLE 关键字
                elif prev_token == 'TABLE':
                    # 检查是否是 CREATE TABLE 语句
                    if i > 1:
                        # 检查是否是 CREATE TABLE 语句
                        create_table = False
                        if i > 2 and tokens[i-3].upper() == 'CREATE':
                            create_table = True
                        
                        # 处理 ALTER TABLE 语句
                        alter_table = False
                        if i > 2 and tokens[i-3].upper() == 'ALTER':
                            alter_table = True
                        
                        # 处理 DROP TABLE 语句
                        drop_table = False
                        if i > 2 and tokens[i-3].upper() == 'DROP':
                            drop_table = True
                        
                        # 处理 CREATE TABLE 语句
                        if create_table:
                            # 加密表名
                            table_name = token.strip('`'"'"'')
                            # 检查是否已经是加密表名
                            if not table_name.startswith('t_') or len(table_name) != 18:
                                # 加密表名
                                encrypted_name = self.encrypt_table_name(table_name)
                                # 保留原始的引号
                                if token.startswith('`') and token.endswith('`'):
                                    encrypted_tokens.append(f"`{encrypted_name}`")
                                elif token.startswith("'") and token.endswith("'"):
                                    encrypted_tokens.append(f"'{encrypted_name}'")
                                elif token.startswith('"') and token.endswith('"'):
                                    encrypted_tokens.append(f'"{encrypted_name}"')
                                else:
                                    encrypted_tokens.append(encrypted_name)
                            else:
                                # 已经是加密表名，直接添加
                                encrypted_tokens.append(token)
                        # 处理 ALTER TABLE 语句
                        elif alter_table:
                            # 加密表名
                            table_name = token.strip('`'"'"'')
                            # 检查是否已经是加密表名
                            if not table_name.startswith('t_') or len(table_name) != 18:
                                # 加密表名
                                encrypted_name = self.encrypt_table_name(table_name)
                                # 保留原始的引号
                                if token.startswith('`') and token.endswith('`'):
                                    encrypted_tokens.append(f"`{encrypted_name}`")
                                elif token.startswith("'") and token.endswith("'"):
                                    encrypted_tokens.append(f"'{encrypted_name}'")
                                elif token.startswith('"') and token.endswith('"'):
                                    encrypted_tokens.append(f'"{encrypted_name}"')
                                else:
                                    encrypted_tokens.append(encrypted_name)
                            else:
                                # 已经是加密表名，直接添加
                                encrypted_tokens.append(token)
                        # 处理 DROP TABLE 语句
                        elif drop_table:
                            # 加密表名
                            table_name = token.strip('`'"'"'')
                            # 检查是否已经是加密表名
                            if not table_name.startswith('t_') or len(table_name) != 18:
                                # 加密表名
                                encrypted_name = self.encrypt_table_name(table_name)
                                # 保留原始的引号
                                if token.startswith('`') and token.endswith('`'):
                                    encrypted_tokens.append(f"`{encrypted_name}`")
                                elif token.startswith("'") and token.endswith("'"):
                                    encrypted_tokens.append(f"'{encrypted_name}'")
                                elif token.startswith('"') and token.endswith('"'):
                                    encrypted_tokens.append(f'"{encrypted_name}"')
                                else:
                                    encrypted_tokens.append(encrypted_name)
                            else:
                                # 已经是加密表名，直接添加
                                encrypted_tokens.append(token)
                        else:
                            # 直接添加 token
                            encrypted_tokens.append(token)
                    else:
                        # 直接添加 token
                        encrypted_tokens.append(token)
                else:
                    encrypted_tokens.append(token)
            else:
                encrypted_tokens.append(token)
            
            i += 1
        
        return ' '.join(encrypted_tokens)
    
    def get_all_encrypted_tables(self):
        """获取所有加密后的表名
        
        Returns:
            list: 加密后的表名列表
        """
        return list(self.table_mapping.values())
    
    def get_all_original_tables(self):
        """获取所有原始表名
        
        Returns:
            list: 原始表名列表
        """
        return list(self.table_mapping.keys())

# 创建表名加密实例
table_encryption = TableEncryption()
