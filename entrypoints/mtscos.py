#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS统一入口模块
整合所有服务，提供统一的服务访问接口
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

# 路径注入：本文件已迁入 entrypoints/，_path_setup.py 已归档至 _config/
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
for _p in (_PROJECT_ROOT, _THIS_DIR, os.path.join(_PROJECT_ROOT, '_config')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import _path_setup

logger = print

try:
    from auth_manager import auth_manager
except Exception as e:
    logger(f"[入口] 加载auth_manager失败: {e}")

try:
    from config_manager import config_manager
except Exception as e:
    logger(f"[入口] 加载config_manager失败: {e}")

try:
    from cache_manager import cache_manager
except Exception as e:
    logger(f"[入口] 加载cache_manager失败: {e}")

try:
    from activity_log_service import activity_log_service
except Exception as e:
    logger(f"[入口] 加载activity_log_service失败: {e}")

try:
    from error_monitor import error_monitor
except Exception as e:
    logger(f"[入口] 加载error_monitor失败: {e}")

try:
    from email_service import email_service
except Exception as e:
    logger(f"[入口] 加载email_service失败: {e}")

try:
    from sms_service import sms_service
except Exception as e:
    logger(f"[入口] 加载sms_service失败: {e}")

try:
    from message_system import message_system
except Exception as e:
    logger(f"[入口] 加载message_system失败: {e}")

try:
    from system_monitor import system_monitor
except Exception as e:
    logger(f"[入口] 加载system_monitor失败: {e}")

try:
    from data_export_service import data_export_service
except Exception as e:
    logger(f"[入口] 加载data_export_service失败: {e}")

try:
    from task_scheduler import task_scheduler
except Exception as e:
    logger(f"[入口] 加载task_scheduler失败: {e}")

try:
    from skill_manager import skill_manager
except Exception as e:
    logger(f"[入口] 加载skill_manager失败: {e}")

try:
    from file_manager import file_manager
except Exception as e:
    logger(f"[入口] 加载file_manager失败: {e}")

try:
    from backup_manager import backup_manager
except Exception as e:
    logger(f"[入口] 加载backup_manager失败: {e}")

try:
    from api_gateway import api_gateway
except Exception as e:
    logger(f"[入口] 加载api_gateway失败: {e}")

try:
    from service_manager import service_manager
except Exception as e:
    logger(f"[入口] 加载service_manager失败: {e}")

try:
    from notification_center import notification_center
except Exception as e:
    logger(f"[入口] 加载notification_center失败: {e}")

try:
    from data_validator import data_validator
except Exception as e:
    logger(f"[入口] 加载data_validator失败: {e}")

class MTSCOS:
    """MTSCOS统一入口"""
    
    def __init__(self):
        self._services = {}
        
        self._register_services()
    
    def _register_services(self):
        """注册服务"""
        services = [
            ('auth', '用户认证服务', auth_manager),
            ('config', '配置管理服务', config_manager),
            ('cache', '数据缓存服务', cache_manager),
            ('log', '活动日志服务', activity_log_service),
            ('error', '错误监控服务', error_monitor),
            ('email', '邮件服务', email_service),
            ('sms', '短信服务', sms_service),
            ('message', '实时消息系统', message_system),
            ('monitor', '系统监控服务', system_monitor),
            ('export', '数据导出服务', data_export_service),
            ('scheduler', '定时任务调度', task_scheduler),
            ('skill', '技能管理服务', skill_manager),
            ('file', '文件管理服务', file_manager),
            ('backup', '系统备份服务', backup_manager),
            ('api', 'API网关服务', api_gateway),
            ('notification', '通知中心服务', notification_center),
            ('validator', '数据验证服务', data_validator)
        ]
        
        for name, description, instance in services:
            if instance:
                self._services[name] = {
                    'description': description,
                    'instance': instance
                }
    
    def get_service(self, name: str):
        """获取服务实例"""
        service = self._services.get(name)
        return service['instance'] if service else None
    
    def get_service_description(self, name: str) -> str:
        """获取服务描述"""
        service = self._services.get(name)
        return service['description'] if service else '未知服务'
    
    def list_services(self) -> List[Dict[str, str]]:
        """列出所有服务"""
        return [
            {'name': name, 'description': service['description']}
            for name, service in self._services.items()
        ]
    
    def start_all(self):
        """启动所有服务"""
        logger(f"[MTSCOS] 开始启动所有服务...")
        
        for name, service in self._services.items():
            instance = service['instance']
            
            if hasattr(instance, 'start'):
                try:
                    instance.start()
                    logger(f"[MTSCOS] ✓ {service['description']} 启动成功")
                except Exception as e:
                    logger(f"[MTSCOS] ✗ {service['description']} 启动失败: {e}")
        
        logger(f"[MTSCOS] 所有服务启动完成")
    
    def stop_all(self):
        """停止所有服务"""
        logger(f"[MTSCOS] 开始停止所有服务...")
        
        for name, service in reversed(list(self._services.items())):
            instance = service['instance']
            
            if hasattr(instance, 'stop'):
                try:
                    instance.stop()
                    logger(f"[MTSCOS] ✓ {service['description']} 停止成功")
                except Exception as e:
                    logger(f"[MTSCOS] ✗ {service['description']} 停止失败: {e}")
        
        logger(f"[MTSCOS] 所有服务停止完成")
    
    def get_status(self) -> Dict[str, Any]:
        """获取整体状态"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'services': {}
        }
        
        for name, service in self._services.items():
            instance = service['instance']
            
            if hasattr(instance, 'get_status'):
                try:
                    status['services'][name] = instance.get_status()
                except Exception as e:
                    status['services'][name] = {'status': 'error', 'error': str(e)}
            else:
                status['services'][name] = {'status': 'available'}
        
        return status
    
    def send_notification(self, title: str, content: str, **kwargs):
        """发送通知"""
        notification = self.get_service('notification')
        if notification:
            return notification.add_notification(title, content, **kwargs)
        return None
    
    def log_activity(self, level: str, log_type: str, action: str, **kwargs):
        """记录活动日志"""
        log_service = self.get_service('log')
        if log_service:
            return log_service.log(level, log_type, action, **kwargs)
        return None
    
    def log_error(self, message: str, **kwargs):
        """记录错误"""
        error_service = self.get_service('error')
        if error_service:
            return error_service.log_error(message, **kwargs)
        return None
    
    def send_email(self, to_email: str, subject: str, content: str, **kwargs):
        """发送邮件"""
        email_svc = self.get_service('email')
        if email_svc:
            return email_svc.send_email(to_email, subject, content, **kwargs)
        return False
    
    def send_sms(self, phone_number: str, message: str, **kwargs):
        """发送短信"""
        sms_svc = self.get_service('sms')
        if sms_svc:
            return sms_svc.send_sms(phone_number, message, **kwargs)
        return False
    
    def execute_skill(self, skill_id: str, **kwargs):
        """执行技能"""
        skill_svc = self.get_service('skill')
        if skill_svc:
            return skill_svc.execute_skill(skill_id, **kwargs)
        return None
    
    def schedule_task(self, task_id: str, name: str, func, **kwargs):
        """调度任务"""
        scheduler = self.get_service('scheduler')
        if scheduler:
            return scheduler.add_task(task_id, name, func, **kwargs)
        return None
    
    def validate_data(self, data: Dict[str, Any], schema: Dict[str, Dict[str, Any]]):
        """验证数据"""
        validator = self.get_service('validator')
        if validator:
            return validator.validate(data, schema)
        return None
    
    def create_backup(self, description: str = None):
        """创建备份"""
        backup_svc = self.get_service('backup')
        if backup_svc:
            return backup_svc.create_backup(description)
        return None
    
    def export_data(self, data: List[Dict[str, Any]], file_format: str = 'json', **kwargs):
        """导出数据"""
        export_svc = self.get_service('export')
        if export_svc:
            return export_svc.export_data(data, file_format, **kwargs)
        return None

mtscos = MTSCOS()

def main():
    """主函数"""
    logger(f"[MTSCOS] MTSCOS AI System")
    logger(f"[MTSCOS] 版本: v9.3.0")
    logger(f"[MTSCOS] ----------------")
    
    mtscos.start_all()
    
    logger(f"[MTSCOS] ----------------")
    logger(f"[MTSCOS] 系统启动完成")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger(f"\n[MTSCOS] 收到停止信号...")
        mtscos.stop_all()
        logger(f"[MTSCOS] 系统已停止")

if __name__ == '__main__':
    main()
