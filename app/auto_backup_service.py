#!/usr/bin/env python3
"""
自动备份服务
实现自动备份、增量备份功能
"""

import os
import shutil
import tarfile
import logging
import time
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class AutoBackupService:
    """自动备份服务"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.backup_path = self.config.get('backup_path', './backups')
        self.backup_interval = self.config.get('backup_interval', 3600)
        self.retention_days = self.config.get('retention_days', 7)
        self.max_count = self.config.get('max_count', 30)
        self.compress_enabled = self.config.get('compress_enabled', True)
        self.encrypt_enabled = self.config.get('encrypt_enabled', False)
        self.include_logs = self.config.get('include_logs', True)
        self.incremental_enabled = self.config.get('incremental_enabled', True)
        self.incremental_interval = self.config.get('incremental_interval', 600)
        self.full_backup_interval = self.config.get('full_backup_interval', 86400)
        self._running = False
        self._last_full_backup = None
        
        os.makedirs(self.backup_path, exist_ok=True)
    
    def _get_backup_filename(self, backup_type: str = 'full') -> str:
        """生成备份文件名"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{backup_type}_{timestamp}.tar.gz"
    
    def _backup_database(self) -> str:
        """备份数据库"""
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
        if os.path.exists(db_path):
            return db_path
        return ""
    
    def _backup_logs(self) -> list:
        """备份日志文件"""
        logs = []
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        if os.path.exists(log_dir):
            for file in os.listdir(log_dir):
                if file.endswith('.log'):
                    logs.append(os.path.join(log_dir, file))
        return logs
    
    def _create_full_backup(self) -> str:
        """创建全量备份"""
        logger.info("创建全量备份")
        
        filename = self._get_backup_filename('full')
        filepath = os.path.join(self.backup_path, filename)
        
        try:
            with tarfile.open(filepath, 'w:gz') as tar:
                db_file = self._backup_database()
                if db_file:
                    tar.add(db_file, arcname='app.db')
                    logger.info(f"已备份数据库: {db_file}")
                
                if self.include_logs:
                    log_files = self._backup_logs()
                    for log_file in log_files:
                        tar.add(log_file, arcname=f'logs/{os.path.basename(log_file)}')
                    logger.info(f"已备份 {len(log_files)} 个日志文件")
            
            self._last_full_backup = datetime.now()
            logger.info(f"全量备份完成: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"创建全量备份失败: {e}")
            if os.path.exists(filepath):
                os.remove(filepath)
            return ""
    
    def _create_incremental_backup(self) -> str:
        """创建增量备份"""
        if not self.incremental_enabled:
            return ""
        
        logger.info("创建增量备份")
        
        filename = self._get_backup_filename('incremental')
        filepath = os.path.join(self.backup_path, filename)
        
        try:
            with tarfile.open(filepath, 'w:gz') as tar:
                db_file = self._backup_database()
                if db_file:
                    tar.add(db_file, arcname='app.db')
                    logger.info(f"已增量备份数据库: {db_file}")
            
            logger.info(f"增量备份完成: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"创建增量备份失败: {e}")
            if os.path.exists(filepath):
                os.remove(filepath)
            return ""
    
    def _cleanup_old_backups(self):
        """清理旧备份"""
        logger.info("清理旧备份")
        
        cutoff_time = datetime.now() - timedelta(days=self.retention_days)
        
        backups = []
        for file in os.listdir(self.backup_path):
            if file.endswith('.tar.gz'):
                filepath = os.path.join(self.backup_path, file)
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                backups.append((filepath, mtime))
        
        backups.sort(key=lambda x: x[1], reverse=True)
        
        deleted_count = 0
        for i, (filepath, mtime) in enumerate(backups):
            if mtime < cutoff_time or i >= self.max_count:
                try:
                    os.remove(filepath)
                    deleted_count += 1
                    logger.info(f"已删除旧备份: {filepath}")
                except Exception as e:
                    logger.error(f"删除备份失败: {filepath}, 错误: {e}")
        
        if deleted_count > 0:
            logger.info(f"共删除 {deleted_count} 个旧备份")
    
    def backup(self, backup_type: str = 'auto') -> str:
        """执行备份"""
        if backup_type == 'full' or (backup_type == 'auto' and 
            (not self._last_full_backup or 
             (datetime.now() - self._last_full_backup).total_seconds() >= self.full_backup_interval)):
            return self._create_full_backup()
        else:
            return self._create_incremental_backup()
    
    def start(self):
        """启动自动备份服务"""
        logger.info(f"启动自动备份服务，间隔: {self.backup_interval}秒")
        self._running = True
        
        while self._running:
            try:
                self.backup()
                self._cleanup_old_backups()
            except Exception as e:
                logger.error(f"自动备份异常: {e}")
            
            for _ in range(self.backup_interval):
                if not self._running:
                    break
                time.sleep(1)
    
    def stop(self):
        """停止自动备份服务"""
        logger.info("停止自动备份服务")
        self._running = False
    
    def backup_on_startup(self):
        """启动时备份"""
        logger.info("启动时执行备份")
        self.backup('full')
    
    def backup_on_shutdown(self):
        """关闭时备份"""
        logger.info("关闭时执行备份")
        self.backup('full')
        self._cleanup_old_backups()

auto_backup_service = AutoBackupService()