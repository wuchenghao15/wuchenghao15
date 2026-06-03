# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
备份管理AI
负责系统备份和恢复功能的AI模块
"""

import time
import threading
import os
from app.utils.logging import logger
from app.models.backup import Backup
import logging
import sys


class BackupManagerAI:
    """备份管理AI:负责系统备份和恢复功能"""

    def __init__(self):
        self.name = "备份管理AI"
        self.description = "负责系统备份和恢复功能的AI模块"
        self.auto_backup_enabled = True
        self.backup_interval = 24 * 3600
        self.max_backup_count = 30
        self.backup_types = ['full', 'incremental']
        self.running = False
        self.thread = None

        self.start_auto_backup()

        logger.info(f"{self.name}初始化完成")

    def start_auto_backup(self):
        """启动自动备份线程"""
        if not self.running and self.auto_backup_enabled:
            self.running = True
            self.thread = threading.Thread(target=self._auto_backup_loop, daemon=True)
            self.thread.start()
            logger.info(f"自动备份功能已启动,备份间隔: {self.backup_interval / 3600}小时")

    def stop_auto_backup(self):
        """停止自动备份线程"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("自动备份功能已停止")

    def _auto_backup_loop(self):
        """自动备份循环"""
        while self.running:
            try:
                self.create_auto_backup()
                self.cleanup_old_backups()
            except Exception as e:
                logger.error(f"自动备份失败: {str(e)}")
            time.sleep(self.backup_interval)

    def create_auto_backup(self):
        """创建自动备份"""
        try:
            backup = Backup(
                name=f"auto_backup_{time.strftime('%Y%m%d_%H%M%S')}",
                backup_type="full",
                created_by="system"
            )

            backup.save()
            backup.create_backup_file()

            logger.info("自动备份创建成功")
            return True
        except Exception as e:
            logger.error(f"创建自动备份失败: {str(e)}")
            return False

    def cleanup_old_backups(self):
        """清理旧备份"""
        try:
            all_backups = Backup.get_all_backups(limit=100)

            if len(all_backups) > self.max_backup_count:
                backups_to_delete = all_backups[self.max_backup_count:]
                for backup in backups_to_delete:
                    Backup.delete_by_id(backup.backup_id)
                    logger.info(f"已清理旧备份: {backup.backup_id}")

            logger.info("备份清理完成")
            return True
        except Exception as e:
            logger.error(f"清理旧备份失败: {str(e)}")
            return False

    def create_backup(self, backup_name=None, backup_type="full", description=None, created_by="system"):
        """创建备份"""
        try:
            backup = Backup(
                name=backup_name,
                backup_type=backup_type,
                description=description,
                created_by=created_by
            )

            backup.save()
            success = backup.create_backup_file()
            if success:
                logger.info(f"手动备份创建成功: {backup_name}")
                return backup
            return None
        except Exception as e:
            logger.error(f"创建备份失败: {str(e)}")
            return None

    def restore_backup(self, backup_id):
        """恢复备份"""
        try:
            success = Backup.restore_backup(backup_id)
            if success:
                logger.info(f"备份恢复成功: {backup_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"恢复备份失败: {str(e)}")
            return False

    def get_backup_stats(self):
        """获取备份统计信息"""
        try:
            all_backups = Backup.get_all_backups(limit=100)
            full_backups = [b for b in all_backups if b.backup_type == 'full' and b.status == 'completed']
            incremental_backups = [b for b in all_backups if b.backup_type == 'incremental' and b.status == 'completed']
            failed_backups = [b for b in all_backups if b.status == 'failed']
            total_size = sum(b.size for b in all_backups if b.status == 'completed')

            latest_full_backup = full_backups[0] if full_backups else None
            latest_incremental_backup = incremental_backups[0] if incremental_backups else None

            stats = {
                'total_backups': len(all_backups),
                'full_backups': len(full_backups),
                'incremental_backups': len(incremental_backups),
                'failed_backups': len(failed_backups),
                'total_size': total_size,
                'latest_full_backup': latest_full_backup.backup_id if latest_full_backup else None,
                'latest_incremental_backup': latest_incremental_backup.backup_id if latest_incremental_backup else None,
                'auto_backup_enabled': self.auto_backup_enabled,
                'backup_interval_hours': self.backup_interval / 3600,
                'max_backup_count': self.max_backup_count
            }

            return stats
        except Exception as e:
            logger.error(f"获取备份统计信息失败: {str(e)}")
            return {}

    def configure_auto_backup(self, enabled, interval_hours, max_count):
        """配置自动备份"""
        try:
            self.auto_backup_enabled = enabled
            self.backup_interval = interval_hours * 3600
            self.max_backup_count = max_count

            self.stop_auto_backup()
            if enabled:
                self.start_auto_backup()

            logger.info(f"自动备份配置更新: enabled={enabled}, interval={interval_hours}h, max_count={max_count}")
            return True
        except Exception as e:
            logger.error(f"配置自动备份失败: {str(e)}")
            return False

    def get_backup_history(self, limit=50, offset=0):
        """获取备份历史"""
        try:
            return Backup.get_all_backups(limit=limit, offset=offset)
        except Exception as e:
            logger.error(f"获取备份历史失败: {str(e)}")
            return []
