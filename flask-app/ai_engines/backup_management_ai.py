#!/usr/bin/env python3
"""
备份管理AI, 负责统一处理所有备份,回滚机制和快照保存
"""

import time
import logging
from datetime import datetime
from app.models.backup import Backup
from app.models.user_snapshots import UserSnapshot
from app.models.enhanced_ai_employee import EnhancedAIEmployee


class BackupManagementAI:
    """备份管理AI, 负责统一处理所有备份,回滚机制和快照保存"""

    def __init__(self):
        self.name = "备份管理AI"
        self.description = "负责统一处理所有备份, 回滚机制和快照保存"
        self.ai_type = "backup_manager"
        self.capabilities = ["backup_management", "rollback_mechanism", "snapshot_saving", "database_unification"]
        self.logger = logging.getLogger("BackupManagementAI")

        self._ensure_tables_created()
        self.backup_employee = self._get_or_create_backup_employee()

    def _ensure_tables_created(self):
        """确保所有必要的表都已创建"""
        try:
            from app.models.backup import Backup
            from app.models.user_snapshots import UserSnapshot
            from app.models.enhanced_ai_employee import EnhancedAIEmployee
            from app.models.ai_brain import AIBrainKnowledge, AIBrainActivity

            UserSnapshot.create_table()
            AIBrainKnowledge.create_table()
            AIBrainActivity.create_table()

            self.logger.info("所有必要的表都已创建完成")
        except Exception as e:
            self.logger.error(f"创建表失败: {str(e)}")
            import traceback
            traceback.print_exc()

    def _get_or_create_backup_employee(self):
        """获取或创建备份管理AI员工"""
        try:
            employees = EnhancedAIEmployee.get_all()
            for employee in employees:
                if employee.ai_type == self.ai_type:
                    self.logger.info(f"找到现有备份管理AI员工: {employee.name} (ID: {employee.employee_id})")
                    return employee

            new_employee = EnhancedAIEmployee.create(
                name=self.name,
                ai_type=self.ai_type,
                description=self.description,
                capabilities=self.capabilities,
                status="active"
            )
            self.logger.info(f"创建新的备份管理AI员工: {new_employee.name} (ID: {new_employee.employee_id})")
            return new_employee
        except Exception as e:
            self.logger.error(f"获取或创建备份管理AI员工失败: {str(e)}")
            return None

    def create_backup(self, backup_type="full", description="", created_by="system"):
        """创建系统备份

        Args:
            backup_type: 备份类型,full或incremental
            description: 备份描述
            created_by: 创建者

        Returns:
            备份ID
        """
        try:
            self.logger.info(f"开始创建备份,类型: {backup_type}, 创建者: {created_by}")

            backup = Backup(
                name=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{backup_type}",
                backup_type=backup_type,
                description=description,
                created_by=created_by
            )

            backup_id = backup.save()
            self.logger.info(f"备份记录已保存到数据库,备份ID: {backup_id}")

            if backup.create_backup_file():
                self.logger.info(f"备份创建成功,备份ID: {backup_id}")
                return backup_id
            else:
                self.logger.error("备份文件创建失败")
                return None
        except Exception as e:
            self.logger.error(f"创建备份失败: {str(e)}")
            return None

    def restore_backup(self, backup_id, created_by="system"):
        """恢复系统备份

        Args:
            backup_id: 备份ID
            created_by: 恢复者

        Returns:
            bool: 是否恢复成功
        """
        try:
            self.logger.info(f"开始恢复备份,备份ID: {backup_id}, 恢复者: {created_by}")

            if Backup.restore_backup(backup_id):
                self.logger.info(f"备份恢复成功,备份ID: {backup_id}")
                return True
            else:
                self.logger.error(f"备份恢复失败,备份ID: {backup_id}")
                return False
        except Exception as e:
            self.logger.error(f"恢复备份失败: {str(e)}")
            return False

    def delete_backup(self, backup_id):
        """删除系统备份

        Args:
            backup_id: 备份ID

        Returns:
            bool: 是否删除成功
        """
        try:
            self.logger.info(f"开始删除备份,备份ID: {backup_id}")

            if Backup.delete_by_id(backup_id):
                self.logger.info(f"备份删除成功,备份ID: {backup_id}")
                return True
            else:
                self.logger.error(f"备份删除失败,备份ID: {backup_id}")
                return False
        except Exception as e:
            self.logger.error(f"删除备份失败: {str(e)}")
            return False

    def create_snapshot(self, user_id, session_id, snapshot_type="system_state", data=None):
        """创建系统或用户快照

        Args:
            user_id: 用户ID
            session_id: 会话ID
            snapshot_type: 快照类型
            data: 快照数据

        Returns:
            快照ID
        """
        try:
            self.logger.info(f"开始创建快照,用户ID: {user_id}, 会话ID: {session_id}, 类型: {snapshot_type}")

            snapshot = UserSnapshot.create(
                user_id=user_id,
                session_id=session_id,
                snapshot_type=snapshot_type,
                data=data or {}
            )

            self.logger.info(f"快照创建成功,快照ID: {snapshot.snapshot_id}")
            return snapshot.snapshot_id
        except Exception as e:
            self.logger.error(f"创建快照失败: {str(e)}")
            return None

    def get_snapshot(self, snapshot_id):
        """获取快照信息

        Args:
            snapshot_id: 快照ID

        Returns:
            快照对象
        """
        try:
            snapshot = UserSnapshot.get_by_id(snapshot_id)
            if snapshot:
                self.logger.info(f"获取快照成功,快照ID: {snapshot_id}")
            else:
                self.logger.warning(f"快照不存在,快照ID: {snapshot_id}")
            return snapshot
        except Exception as e:
            self.logger.error(f"获取快照失败: {str(e)}")
            return None

    def delete_snapshot(self, snapshot_id):
        """删除快照

        Args:
            snapshot_id: 快照ID

        Returns:
            bool: 是否删除成功
        """
        try:
            snapshot = UserSnapshot.get_by_id(snapshot_id)
            if snapshot:
                if snapshot.delete():
                    self.logger.info(f"快照删除成功,快照ID: {snapshot_id}")
                    return True
            return False
        except Exception as e:
            self.logger.error(f"删除快照失败: {str(e)}")
            return False

    def get_all_backups(self, limit=50, offset=0):
        """获取所有备份

        Args:
            limit: 限制数量
            offset: 偏移量

        Returns:
            备份列表
        """
        try:
            backups = Backup.get_all_backups(limit=limit, offset=offset)
            self.logger.info(f"获取备份列表成功,数量: {len(backups)}")
            return backups
        except Exception as e:
            self.logger.error(f"获取备份列表失败: {str(e)}")
            return []

    def get_all_snapshots(self, limit=50):
        """获取所有快照

        Args:
            limit: 限制数量

        Returns:
            快照列表
        """
        try:
            snapshots = UserSnapshot.get_latest(limit=limit)
            self.logger.info(f"获取快照列表成功,数量: {len(snapshots)}")
            return snapshots
        except Exception as e:
            self.logger.error(f"获取快照列表失败: {str(e)}")
            return []

    def clean_old_backups(self, keep_days=30):
        """清理旧备份

        Args:
            keep_days: 保留天数

        Returns:
            删除的备份数量
        """
        try:
            self.logger.info(f"开始清理旧备份,保留天数: {keep_days}")

            keep_threshold = time.time() - (keep_days * 24 * 3600)

            all_backups = Backup.get_all_backups(limit=1000, offset=0)
            deleted_count = 0

            for backup in all_backups:
                if backup.created_at < keep_threshold:
                    if Backup.delete_by_id(backup.backup_id):
                        deleted_count += 1

            self.logger.info(f"清理旧备份完成,删除数量: {deleted_count}")
            return deleted_count
        except Exception as e:
            self.logger.error(f"清理旧备份失败: {str(e)}")
            return 0

    def get_backup_stats(self):
        """获取备份统计信息

        Returns:
            统计信息字典
        """
        try:
            total_backups = Backup.get_backup_count()

            latest_full_backup = Backup.get_latest_backup(backup_type="full")
            latest_incremental_backup = Backup.get_latest_backup(backup_type="incremental")

            snapshots = UserSnapshot.get_latest(limit=1)
            total_snapshots = snapshots[0].snapshot_id if snapshots else 0

            stats = {
                "total_backups": total_backups,
                "latest_full_backup": {
                    "id": latest_full_backup.backup_id if latest_full_backup else None,
                    "created_at": latest_full_backup.created_at if latest_full_backup else None,
                    "size": latest_full_backup.size if latest_full_backup else None
                },
                "latest_incremental_backup": {
                    "id": latest_incremental_backup.backup_id if latest_incremental_backup else None,
                    "created_at": latest_incremental_backup.created_at if latest_incremental_backup else None,
                    "size": latest_incremental_backup.size if latest_incremental_backup else 0
                },
                "total_snapshots": total_snapshots
            }

            self.logger.info("获取备份统计信息成功")
            return stats
        except Exception as e:
            self.logger.error(f"获取备份统计信息失败: {str(e)}")
            return {}

    def auto_backup(self):
        """执行自动备份

        Returns:
            备份ID
        """
        try:
            self.logger.info("开始执行自动备份")

            backup_id = self.create_backup(
                backup_type="full",
                description="自动备份",
                created_by="backup_management_ai"
            )

            if backup_id:
                self.logger.info(f"自动备份执行成功,备份ID: {backup_id}")
            else:
                self.logger.error("自动备份执行失败")

            return backup_id
        except Exception as e:
            self.logger.error(f"自动备份失败: {str(e)}")
            return None

    def rollback_to_snapshot(self, snapshot_id):
        """回滚到指定快照

        Args:
            snapshot_id: 快照ID

        Returns:
            bool: 是否回滚成功
        """
        try:
            self.logger.info(f"开始回滚到快照,快照ID: {snapshot_id}")

            snapshot = UserSnapshot.get_by_id(snapshot_id)
            if not snapshot:
                self.logger.error(f"快照不存在,快照ID: {snapshot_id}")
                return False

            if snapshot.restore():
                self.logger.info(f"回滚到快照成功,快照ID: {snapshot_id}")
                return True
            else:
                self.logger.error(f"回滚到快照失败,快照ID: {snapshot_id}")
                return False
        except Exception as e:
            self.logger.error(f"回滚到快照失败: {str(e)}")
            return False


backup_management_ai = BackupManagementAI()
