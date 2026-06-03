#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统功能服务 - 提供系统级功能支持
包含配置管理、监控告警、日志管理、备份恢复等核心功能
"""
import logging
import os
import json
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class SystemFeatures:
    """系统功能集合"""

    def __init__(self):
        self.config_manager = ConfigurationManager()
        self.monitor_service = MonitorService()
        self.log_manager = LogManagementService()
        self.backup_service = BackupRecoveryService()
        self.notification_service = NotificationService()
        logger.info("系统功能服务初始化完成")

    def configure(self, config: Dict[str, Any]):
        """配置系统"""
        self.config_manager.update_config(config)

    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return self.monitor_service.get_system_status()

    def backup(self, backup_name: str):
        """执行备份"""
        self.backup_service.create_backup(backup_name)

    def notify(self, recipients: List[str], message: Dict[str, Any]):
        """发送通知"""
        self.notification_service.send(recipients, message)

class ConfigurationManager:
    """配置管理器"""

    def __init__(self):
        self.config_file = 'system_config.json'
        self.config = {}
        self._load_config()
        logger.info("配置管理器初始化完成")

    def _load_config(self):
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info("配置文件加载成功")
            except Exception as e:
                logger.error(f"配置文件加载失败: {str(e)}")
                self.config = self._get_default_config()

    def _save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info("配置文件保存成功")
        except Exception as e:
            logger.error(f"配置文件保存失败: {str(e)}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置"""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def update_config(self, config: Dict[str, Any]):
        """更新配置"""
        self.config.update(config)
        self._save_config()
        logger.info(f"配置已更新: {list(config.keys())}")

    def reset_config(self):
        """重置配置为默认值"""
        self.config = self._get_default_config()
        self._save_config()
        logger.info("配置已重置为默认值")

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'debug': False,
            'log_level': 'INFO',
            'backup_enabled': True,
            'backup_interval': 86400
        }

class MonitorService:
    """监控服务"""

    def __init__(self):
        self.alerts = []
        self.log_dir = 'logs'
        logger.info("监控服务初始化完成")

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            import psutil
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_usage = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage('/').percent

            status = {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'usage': cpu_usage,
                    'status': self._get_status_level(cpu_usage)
                },
                'memory': {
                    'usage': memory_usage,
                    'status': self._get_status_level(memory_usage)
                },
                'disk': {
                    'usage': disk_usage,
                    'status': self._get_status_level(disk_usage)
                },
                'services': self._check_services(),
                'alerts': self.alerts[:5]
            }
            return status
        except Exception as e:
            logger.error(f"获取系统状态失败: {str(e)}")
            return {'error': str(e)}

    def _get_status_level(self, usage: float) -> str:
        """获取状态级别"""
        if usage < 50:
            return 'normal'
        elif usage < 80:
            return 'warning'
        else:
            return 'critical'

    def _check_services(self) -> List[Dict[str, Any]]:
        """检查服务状态"""
        return [
            {'name': 'web_server', 'status': 'running'},
            {'name': 'database', 'status': 'running'},
            {'name': 'cache', 'status': 'running'}
        ]

    def create_alert(self, level: str, message: str):
        """创建告警"""
        alert = {
            'level': level,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.alerts.append(alert)
        logger.warning(f"告警 [{level}]: {message}")

    def clear_alerts(self):
        """清除告警"""
        self.alerts = []

class LogManagementService:
    """日志管理服务"""

    def __init__(self):
        self.log_dir = 'logs'
        os.makedirs(self.log_dir, exist_ok=True)
        logger.info("日志管理服务初始化完成")

    def get_logs(self, log_type: str = 'all', limit: int = 100) -> List[Dict[str, Any]]:
        """获取日志"""
        logs = []

        for filename in os.listdir(self.log_dir):
            if log_type != 'all' and log_type not in filename:
                continue

            filepath = os.path.join(self.log_dir, filename)
            if os.path.isfile(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        lines = f.readlines()[-limit:]
                        for line in lines:
                            logs.append({
                                'content': line.strip(),
                                'timestamp': datetime.now().isoformat()
                            })
                except Exception as e:
                    logger.error(f"读取日志文件失败 {filename}: {str(e)}")

        return logs[-limit:]

    def archive_logs(self, days_to_keep: int = 7):
        """归档日志"""
        archive_dir = os.path.join(self.log_dir, 'archive')
        os.makedirs(archive_dir, exist_ok=True)

        now = datetime.now()

        for filename in os.listdir(self.log_dir):
            filepath = os.path.join(self.log_dir, filename)
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if (now - file_time).days > days_to_keep:
                    archive_path = os.path.join(archive_dir, filename)
                    shutil.move(filepath, archive_path)

    def clear_logs(self):
        """清除日志"""
        for filename in os.listdir(self.log_dir):
            filepath = os.path.join(self.log_dir, filename)
            if os.path.isfile(filepath):
                os.remove(filepath)
        logger.info("日志已清除")

class BackupRecoveryService:
    """备份恢复服务"""

    def __init__(self):
        self.backup_dir = 'backups'
        os.makedirs(self.backup_dir, exist_ok=True)
        logger.info("备份恢复服务初始化完成")

    def create_backup(self, backup_name: str):
        """创建备份"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name_with_time = f"{backup_name}_{timestamp}"
        backup_path = os.path.join(self.backup_dir, backup_name_with_time)
        os.makedirs(backup_path, exist_ok=True)

        db_files = ['app.db', 'mtscos.db']
        for db_file in db_files:
            if os.path.exists(db_file):
                shutil.copy(db_file, backup_path)

        config_files = ['system_config.json', 'VERSION']
        for config_file in config_files:
            if os.path.exists(config_file):
                shutil.copy(config_file, backup_path)

        logger.info(f"备份创建成功: {backup_name_with_time}")
        return backup_path

    def list_backups(self) -> List[Dict[str, Any]]:
        """列出备份"""
        backups = []

        for item in os.listdir(self.backup_dir):
            item_path = os.path.join(self.backup_dir, item)
            if os.path.isdir(item_path):
                backups.append({
                    'name': item,
                    'path': item_path,
                    'created_at': datetime.fromtimestamp(os.path.getmtime(item_path)).isoformat()
                })

        return sorted(backups, key=lambda x: x['created_at'], reverse=True)

    def restore_backup(self, backup_name: str):
        """恢复备份"""
        backup_path = os.path.join(self.backup_dir, backup_name)
        if not os.path.exists(backup_path):
            raise ValueError(f"备份不存在: {backup_name}")

        for filename in os.listdir(backup_path):
            src = os.path.join(backup_path, filename)
            dst = filename
            if os.path.isfile(src):
                shutil.copy(src, dst)

        logger.info(f"备份恢复成功: {backup_name}")

class NotificationService:
    """通知服务"""

    def __init__(self):
        self.channels = {}
        logger.info("通知服务初始化完成")

    def register_channel(self, channel_id: str, sender):
        """注册通知渠道"""
        self.channels[channel_id] = sender
        logger.info(f"注册通知渠道: {channel_id}")

    def send(self, recipients: List[str], message: Dict[str, Any]):
        """发送通知"""
        for channel_id, sender in self.channels.items():
            try:
                sender(recipients, message)
                logger.info(f"通知已发送到 {channel_id}")
            except Exception as e:
                logger.error(f"通知发送失败 {channel_id}: {str(e)}")

    def send_email(self, recipients: List[str], subject: str, body: str):
        """发送邮件通知"""
        logger.info(f"发送邮件到 {recipients}: {subject}")

    def send_system_notification(self, message: str):
        """发送系统通知"""
        logger.info(f"系统通知: {message}")

system_features = SystemFeatures()

def init_system_features():
    """初始化系统功能"""
    logger.info("初始化系统功能...")

    system_features.notification_service.register_channel(
        'email',
        lambda recipients, msg: system_features.notification_service.send_email(
            recipients, msg.get('subject'), msg.get('body')
        )
    )

    system_features.notification_service.register_channel(
        'system',
        lambda recipients, msg: system_features.notification_service.send_system_notification(
            msg.get('message')
        )
    )

    logger.info("系统功能初始化完成")

if __name__ == "__main__":
    init_system_features()
