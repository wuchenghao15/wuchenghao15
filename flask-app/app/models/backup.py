# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
备份管理模型
用于处理系统备份和恢复功能
"""

import sqlite3
from contextlib import contextmanager
import os
import time
import datetime
import zipfile
from app.config import Config
from app.utils.logging import logger
import logging
import sys


class Backup:
    """备份管理模型"""

    def __init__(self, backup_id=None, name=None, backup_type="full", description=None, size=0, status="created",
                 created_at=None, created_by="system", file_path=None, checksum=None):
        self.backup_id = backup_id
        self.name = name
        self.backup_type = backup_type
        self.description = description
        self.size = size
        self.status = status
        self.created_at = created_at or time.time()
        self.created_by = created_by
        self.file_path = file_path
        self.checksum = checksum

    @staticmethod
    def _connect_db():
        """连接数据库"""
        return sqlite3.connect(Config.DATABASE_PATH)

    def save(self):
        """保存备份记录"""
        conn = Backup._connect_db()
        cursor = conn.cursor()
        if self.backup_id:
            cursor.execute('''
                UPDATE backups SET name=?, backup_type=?, description=?, size=?, status=?, created_at=?, created_by=?, file_path=?, checksum=? WHERE id=?
            ''', (self.name, self.backup_type, self.description, self.size, self.status, self.created_at, self.created_by, self.file_path, self.checksum, self.backup_id))
        else:
            cursor.execute('''
                INSERT INTO backups (name, backup_type, description, size, status, created_at, created_by, file_path, checksum)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.name, self.backup_type, self.description, self.size, self.status, self.created_at, self.created_by, self.file_path, self.checksum))
            self.backup_id = cursor.lastrowid

        conn.commit()
        conn.close()
        return self.backup_id

    def create_backup_file(self):
        """创建备份文件"""
        try:
            backup_dir = os.path.join(os.path.dirname(Config.DATABASE_PATH), 'backups')
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)

            timestamp = datetime.datetime.fromtimestamp(self.created_at).strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{timestamp}_{self.backup_type}.zip"
            backup_path = os.path.join(backup_dir, backup_filename)

            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if os.path.exists(Config.DATABASE_PATH):
                    zipf.write(Config.DATABASE_PATH, os.path.basename(Config.DATABASE_PATH))
                    logger.info(f"备份数据库文件: {Config.DATABASE_PATH}")

                config_files = [
                    os.path.join(os.path.dirname(__file__), '..', '..', 'VERSION')
                ]

                for config_file in config_files:
                    if os.path.exists(config_file):
                        arcname = os.path.relpath(config_file, os.path.dirname(os.path.dirname(__file__)))
                        zipf.write(config_file, arcname)
                        logger.info(f"备份配置文件: {config_file}")

            self.file_path = backup_path
            self.size = os.path.getsize(backup_path)
            self.status = 'completed'
            self.save()

            logger.info(f"备份文件创建成功: {backup_path}")
            return True

        except Exception as e:
            self.status = 'failed'
            self.save()
            logger.error(f"创建备份文件失败: {str(e)}")
            return False
