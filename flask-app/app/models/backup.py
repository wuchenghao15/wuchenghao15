#!/usr/bin/env python3
"""
备份管理模型
用于处理系统备份和恢复功能
"""

import sqlite3
import os
import time
import datetime
import zipfile
from app.config import Config
from app.utils.logging import logger


class Backup:
    """备份管理模型"""
    
    def __init__(self, backup_id=None, name=None, backup_type="full", description=None, size=0, status="created", 
                 created_at=None, created_by="system", file_path=None, checksum=None):
        self.backup_id = backup_id
        self.name = name
        self.backup_type = backup_type  # full, incremental
        self.description = description
        self.size = size
        self.status = status  # created, running, completed, failed
        self.created_at = created_at or time.time()
        self.created_by = created_by
        self.file_path = file_path
        self.checksum = checksum
    
    @staticmethod
    def _connect_db():
        """连接数据库"""
        return sqlite3.connect(Config.DATABASE_PATH)
    
    @staticmethod
    def create_table():
        """创建备份表"""
        conn = Backup._connect_db()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                backup_type TEXT NOT NULL DEFAULT 'full',
                description TEXT,
                size INTEGER DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'created',
                created_at REAL,
                created_by TEXT NOT NULL DEFAULT 'system',
                file_path TEXT,
                checksum TEXT
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("备份表创建成功")
    
    def save(self):
        """保存备份记录"""
        conn = Backup._connect_db()
        cursor = conn.cursor()
        
        if self.backup_id:
            # 更新现有备份
            cursor.execute('''
                UPDATE backups SET name=?, backup_type=?, description=?, size=?, status=?, created_at=?, created_by=?, file_path=?, checksum=? WHERE id=?
            ''', (self.name, self.backup_type, self.description, self.size, self.status, self.created_at, self.created_by, self.file_path, self.checksum, self.backup_id))
        else:
            # 创建新备份
            cursor.execute('''
                INSERT INTO backups (name, backup_type, description, size, status, created_at, created_by, file_path, checksum) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.name, self.backup_type, self.description, self.size, self.status, self.created_at, self.created_by, self.file_path, self.checksum))
            self.backup_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return self.backup_id
    
    @staticmethod
    def get_by_id(backup_id):
        """通过ID获取备份"""
        conn = Backup._connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM backups WHERE id=?', (backup_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Backup(
                backup_id=row[0],
                name=row[1],
                backup_type=row[2],
                description=row[3],
                size=row[4],
                status=row[5],
                created_at=row[6],
                created_by=row[7],
                file_path=row[8],
                checksum=row[9]
            )
        return None
    
    @staticmethod
    def get_all_backups(limit=50, offset=0):
        """获取所有备份"""
        conn = Backup._connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM backups ORDER BY created_at DESC LIMIT ? OFFSET ?', (limit, offset))
        rows = cursor.fetchall()
        conn.close()
        
        backups = []
        for row in rows:
            backups.append(Backup(
                backup_id=row[0],
                name=row[1],
                backup_type=row[2],
                description=row[3],
                size=row[4],
                status=row[5],
                created_at=row[6],
                created_by=row[7],
                file_path=row[8],
                checksum=row[9]
            ))
        return backups
    
    @staticmethod
    def get_backup_count():
        """获取备份总数"""
        conn = Backup._connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM backups')
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    @staticmethod
    def delete_by_id(backup_id):
        """通过ID删除备份"""
        # 先获取备份记录
        backup = Backup.get_by_id(backup_id)
        if backup:
            # 删除备份文件
            if backup.file_path and os.path.exists(backup.file_path):
                try:
                    os.remove(backup.file_path)
                    logger.info(f"删除备份文件: {backup.file_path}")
                except Exception as e:
                    logger.error(f"删除备份文件失败: {str(e)}")
            
            # 删除数据库记录
            conn = Backup._connect_db()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM backups WHERE id=?', (backup_id,))
            conn.commit()
            conn.close()
            logger.info(f"删除备份记录: {backup_id}")
            return True
        return False
    
    def create_backup_file(self):
        """创建备份文件"""
        try:
            # 创建备份目录
            backup_dir = os.path.join(os.path.dirname(Config.DATABASE_PATH), 'backups')
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # 生成备份文件名
            timestamp = datetime.datetime.fromtimestamp(self.created_at).strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{timestamp}_{self.backup_type}.zip"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # 创建备份文件
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 备份数据库文件
                if os.path.exists(Config.DATABASE_PATH):
                    zipf.write(Config.DATABASE_PATH, os.path.basename(Config.DATABASE_PATH))
                    logger.info(f"备份数据库文件: {Config.DATABASE_PATH}")
                
                # 备份配置文件
                config_files = [
                    os.path.join(os.path.dirname(__file__), '..', 'config.py'),
                    os.path.join(os.path.dirname(__file__), '..', '..', 'VERSION')
                ]
                
                for config_file in config_files:
                    if os.path.exists(config_file):
                        arcname = os.path.relpath(config_file, os.path.dirname(os.path.dirname(__file__)))
                        zipf.write(config_file, arcname)
                        logger.info(f"备份配置文件: {config_file}")
            
            # 更新备份记录
            self.file_path = backup_path
            self.size = os.path.getsize(backup_path)
            self.status = 'completed'
            self.save()
            
            logger.info(f"备份文件创建成功: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"创建备份文件失败: {str(e)}")
            self.status = 'failed'
            self.save()
            return False
    
    @staticmethod
    def restore_backup(backup_id):
        """恢复备份"""
        try:
            # 获取备份记录
            backup = Backup.get_by_id(backup_id)
            if not backup:
                logger.error(f"备份不存在: {backup_id}")
                return False
            
            if backup.status != 'completed':
                logger.error(f"备份状态异常，无法恢复: {backup.status}")
                return False
            
            if not backup.file_path or not os.path.exists(backup.file_path):
                logger.error(f"备份文件不存在: {backup.file_path}")
                return False
            
            # 先创建当前状态的备份作为回退
            fallback_backup = Backup(
                name=f"fallback_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
                backup_type="full",
                description="恢复前的回退备份",
                created_by="system"
            )
            fallback_backup.save()
            fallback_backup.create_backup_file()
            
            # 解压备份文件
            with zipfile.ZipFile(backup.file_path, 'r') as zipf:
                # 恢复数据库文件
                db_filename = os.path.basename(Config.DATABASE_PATH)
                if db_filename in zipf.namelist():
                    # 先关闭所有数据库连接
                    # 恢复数据库文件
                    zipf.extract(db_filename, os.path.dirname(Config.DATABASE_PATH))
                    logger.info(f"恢复数据库文件: {Config.DATABASE_PATH}")
                
                # 恢复配置文件
                for file_info in zipf.infolist():
                    if file_info.filename.endswith('.py') or file_info.filename == 'VERSION':
                        extract_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), file_info.filename)
                        os.makedirs(os.path.dirname(extract_path), exist_ok=True)
                        zipf.extract(file_info, os.path.dirname(os.path.dirname(__file__)))
                        logger.info(f"恢复配置文件: {extract_path}")
            
            logger.info(f"备份恢复成功: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"恢复备份失败: {str(e)}")
            return False
    
    @staticmethod
    def get_latest_backup(backup_type="full"):
        """获取最新的备份"""
        conn = Backup._connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM backups WHERE backup_type=? AND status=? ORDER BY created_at DESC LIMIT 1', 
                      (backup_type, 'completed'))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Backup(
                backup_id=row[0],
                name=row[1],
                backup_type=row[2],
                description=row[3],
                size=row[4],
                status=row[5],
                created_at=row[6],
                created_by=row[7],
                file_path=row[8],
                checksum=row[9]
            )
        return None
