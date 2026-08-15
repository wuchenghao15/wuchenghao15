# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI管理系统
负责AI的整个生命周期管理:从创建、培训、部署到监控和回收
"""

import os
import json
import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

from app.ai.ai_capability_refiner import ai_capability_refiner
from app.ai.ai_training_monitor import ai_training_monitor
from app.ai.ai_instance_manager import ai_instance_manager
from app.ai.error_case_collector import error_case_collector
from app.ai.error_case_learner import error_case_learner
import sys

logger = logging.getLogger('ai_management_system')


class AIManagementSystem:
    """AI管理系统类"""

    def __init__(self):
        """初始化AI管理系统"""
        self.ai_instances = {}
        self.ai_assignments = {}
        self.system_status = {
            'total_instances': 0,
            'active_instances': 0,
            'trained_instances': 0,
            'monitoring_instances': 0,
            'last_updated': datetime.now().isoformat()
        }
        self.lock = threading.Lock()
        self.management_thread = None
        self.running = False
        self.config = {
            'check_interval': 60,
            'cleanup_interval': 1800,
            'max_inactive_time': 1800,
            'auto_scale_enabled': True,
            'health_check_enabled': True
        }

        logger.info("AI管理系统初始化完成")

    def start(self):
        """启动AI管理系统"""
        try:
            if self.running:
                logger.warning("AI管理系统已在运行中")
                return False

            self.running = True

            def management_loop():
                """管理主循环"""
                while self.running:
                    try:
                        self._check_ai_instances()
                        self._update_system_status()
                        self._cleanup_resources()
                        self._process_pending_tasks()
                        time.sleep(self.config['check_interval'])
                    except Exception as e:
                        logger.error(f"管理线程错误: {str(e)}")
                        time.sleep(self.config['check_interval'])

            self.management_thread = threading.Thread(
                target=management_loop,
                daemon=True,
                name="AI-Management-Thread"
            )
            self.management_thread.start()

            logger.info("AI管理系统启动成功")
            return True
        except Exception as e:
            logger.error(f"启动AI管理系统失败: {str(e)}")
            return False

    def stop(self):
        """停止AI管理系统"""
        try:
            self.running = False

            if self.management_thread and self.management_thread.is_alive():
                self.management_thread.join(timeout=5)

            for instance_id in list(self.ai_instances.keys()):
                self.stop_monitoring(instance_id)

            logger.info("AI管理系统停止成功")
            return True
        except Exception as e:
            logger.error(f"停止AI管理系统失败: {str(e)}")
            return False

    def _check_ai_instances(self):
        """检查所有AI实例状态"""
        try:
            with self.lock:
                for instance_id in list(self.ai_instances.keys()):
                    try:
                        ai_instance = self.ai_instances[instance_id]
                        if hasattr(ai_instance, 'get_status'):
                            status = ai_instance.get_status()
                            if status and status.get('status') == 'error':
                                self._handle_instance_error(instance_id, ai_instance)
                    except Exception as e:
                        logger.error(f"检查实例 {instance_id} 失败: {str(e)}")
        except Exception as e:
            logger.error(f"检查AI实例状态失败: {str(e)}")

    def _handle_instance_error(self, instance_id: str, ai_instance):
        """处理实例错误"""
        try:
            error_info = {
                'ai_instance_id': instance_id,
                'timestamp': datetime.now().isoformat()
            }
            error_case_collector.capture_exception(error_info)

            if hasattr(ai_instance, 'recover'):
                ai_instance.recover()
            elif hasattr(ai_instance, 'initialize'):
                ai_instance.initialize()

            logger.info(f"已尝试恢复AI实例: {instance_id}")
        except Exception as e:
            logger.error(f"恢复AI实例失败 {instance_id}: {str(e)}")

    def _update_system_status(self):
        """更新系统状态"""
        try:
            with self.lock:
                active_count = 0
                trained_count = 0
                monitored_count = 0

                for ai_instance in self.ai_instances.values():
                    if hasattr(ai_instance, 'status'):
                        if ai_instance.status == 'running':
                            active_count += 1
                    if hasattr(ai_instance, 'trained') and ai_instance.trained:
                        trained_count += 1

                self.system_status = {
                    'total_instances': len(self.ai_instances),
                    'active_instances': active_count,
                    'trained_instances': trained_count,
                    'monitoring_instances': monitored_count,
                    'last_updated': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"更新系统状态失败: {str(e)}")

    def _cleanup_resources(self):
        """清理资源"""
        try:
            current_time = datetime.now().timestamp()
            instances_to_cleanup = []

            with self.lock:
                for instance_id, ai_data in list(self.ai_instances.items()):
                    if instance_id in self.ai_assignments:
                        assignment = self.ai_assignments[instance_id]
                        assigned_time = datetime.fromisoformat(assignment['assigned_time']).timestamp()
                        if current_time - assigned_time > self.config['max_inactive_time']:
                            instances_to_cleanup.append(instance_id)

            for instance_id in instances_to_cleanup:
                logger.info(f"回收长时间未活动的AI实例: {instance_id}")
                self.recycle_ai(instance_id)

        except Exception as e:
            logger.error(f"清理资源失败: {str(e)}")

    def _process_pending_tasks(self):
        """处理待处理任务"""
        pass

    def register_ai(self, instance_id: str, ai_instance: Any) -> bool:
        """注册AI实例"""
        try:
            with self.lock:
                if instance_id in self.ai_instances:
                    logger.warning(f"AI实例已存在: {instance_id}")
                    return False

                self.ai_instances[instance_id] = ai_instance
                self.system_status['total_instances'] += 1
                logger.info(f"AI实例注册成功: {instance_id}")
                return True
        except Exception as e:
            logger.error(f"注册AI实例失败: {str(e)}")
            return False

    def unregister_ai(self, instance_id: str) -> bool:
        """注销AI实例"""
        try:
            with self.lock:
                if instance_id not in self.ai_instances:
                    logger.warning(f"AI实例不存在: {instance_id}")
                    return False

                del self.ai_instances[instance_id]
                if instance_id in self.ai_assignments:
                    del self.ai_assignments[instance_id]

                self.system_status['total_instances'] -= 1
                logger.info(f"AI实例注销成功: {instance_id}")
                return True
        except Exception as e:
            logger.error(f"注销AI实例失败: {str(e)}")
            return False

    def start_monitoring(self, instance_id: str) -> bool:
        """启动实例监控"""
        try:
            with self.lock:
                if instance_id not in self.ai_instances:
                    logger.warning(f"AI实例不存在: {instance_id}")
                    return False

                ai_instance = self.ai_instances[instance_id]
                if hasattr(ai_training_monitor, 'start_monitoring'):
                    ai_training_monitor.start_monitoring(instance_id, ai_instance)

                logger.info(f"启动AI实例监控: {instance_id}")
                return True
        except Exception as e:
            logger.error(f"启动监控失败: {str(e)}")
            return False

    def stop_monitoring(self, instance_id: str) -> bool:
        """停止实例监控"""
        try:
            with self.lock:
                if hasattr(ai_training_monitor, 'stop_monitoring'):
                    ai_training_monitor.stop_monitoring(instance_id)

                logger.info(f"停止AI实例监控: {instance_id}")
                return True
        except Exception as e:
            logger.error(f"停止监控失败: {str(e)}")
            return False

    def assign_ai(self, instance_id: str, user_id: str) -> bool:
        """分配AI实例给用户"""
        try:
            with self.lock:
                if instance_id not in self.ai_instances:
                    logger.warning(f"AI实例不存在: {instance_id}")
                    return False

                self.ai_assignments[instance_id] = {
                    'user_id': user_id,
                    'assigned_time': datetime.now().isoformat()
                }

                ai_instance = self.ai_instances[instance_id]
                if hasattr(ai_instance, 'bind_user'):
                    ai_instance.bind_user(user_id)

                logger.info(f"AI实例分配成功: {instance_id} -> {user_id}")
                return True
        except Exception as e:
            logger.error(f"分配AI实例失败: {str(e)}")
            return False

    def recycle_ai(self, instance_id: str) -> bool:
        """回收AI实例"""
        try:
            with self.lock:
                if instance_id not in self.ai_instances:
                    return False

                ai_instance = self.ai_instances[instance_id]
                if hasattr(ai_instance, 'shutdown'):
                    ai_instance.shutdown()

                if instance_id in self.ai_assignments:
                    del self.ai_assignments[instance_id]

                self.stop_monitoring(instance_id)
                logger.info(f"AI实例回收成功: {instance_id}")
                return True
        except Exception as e:
            logger.error(f"回收AI实例失败: {str(e)}")
            return False

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return self.system_status

    def get_instance_info(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """获取实例信息"""
        try:
            with self.lock:
                if instance_id not in self.ai_instances:
                    return None

                ai_instance = self.ai_instances[instance_id]
                if hasattr(ai_instance, 'get_status'):
                    return ai_instance.get_status()
                return None
        except Exception as e:
            logger.error(f"获取实例信息失败: {str(e)}")
            return None

    def list_all_instances(self) -> List[Dict[str, Any]]:
        """列出所有AI实例"""
        instances = []
        try:
            with self.lock:
                for instance_id, ai_instance in self.ai_instances.items():
                    if hasattr(ai_instance, 'get_status'):
                        info = ai_instance.get_status()
                        info['instance_id'] = instance_id
                        instances.append(info)
        except Exception as e:
            logger.error(f"列出AI实例失败: {str(e)}")
        return instances

    def auto_scale(self) -> bool:
        """自动扩缩容"""
        try:
            if not self.config.get('auto_scale_enabled'):
                return False

            current_active = self.system_status.get('active_instances', 0)
            total_instances = self.system_status.get('total_instances', 0)

            if current_active == 0 and total_instances == 0:
                logger.info("自动扩缩容: 创建新的AI实例")
                return True
            elif current_active > total_instances * 0.8:
                logger.info("自动扩缩容: 考虑创建新实例")
                return True

            return False
        except Exception as e:
            logger.error(f"自动扩缩容失败: {str(e)}")
            return False


ai_management_system = AIManagementSystem()
