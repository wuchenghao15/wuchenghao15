# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
AI实例管理器模块
负责管理AI实例的生命周期
r"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(r'ai_instance_manager')


class AIInstanceManager:
    r"""AI实例管理器类r"""

    def __init__(self):
        r"""初始化AI实例管理器r"""
        self.instances = {}
        self.instance_counter = 0
        logger.info(r"AI实例管理器初始化完成")

    def register_instance(self, ai_instance: Any) -> bool:
        r"""注册AI实例r"""
        try:
            instance_id = ai_instance.instance_id
            if instance_id not in self.instances:
                self.instances[instance_id] = ai_instance
                self.instance_counter += 1
                logger.info(fr"AI实例注册成功: {instance_id}")
                return True
            else:
                logger.warning(fr"AI实例已存在: {instance_id}")
                return False
        except Exception as e:
            logger.error(fr"注册AI实例失败: {str(e)}")
            return False

    def unregister_instance(self, instance_id: str) -> bool:
        r"""注销AI实例r"""
        try:
            if instance_id in self.instances:
                del self.instances[instance_id]
                self.instance_counter -= 1
                logger.info(fr"AI实例注销成功: {instance_id}")
                return True
            else:
                logger.warning(fr"AI实例不存在: {instance_id}")
                return False
        except Exception as e:
            logger.error(fr"注销AI实例失败: {str(e)}")
            return False

    def get_instance(self, instance_id: str) -> Optional[Any]:
        r"""获取AI实例r"""
        return self.instances.get(instance_id)

    def get_all_instances(self) -> List[Any]:
        r"""获取所有AI实例r"""
        return list(self.instances.values())

    def shutdown_instance(self, instance_id: str) -> bool:
        r"""关闭AI实例r"""
        try:
            instance = self.instances.get(instance_id)
            if instance:
                instance.shutdown()
                self.unregister_instance(instance_id)
                logger.info(fr"AI实例关闭成功: {instance_id}")
                return True
            else:
                logger.warning(fr"AI实例不存在: {instance_id}")
                return False
        except Exception as e:
            logger.error(fr"关闭AI实例失败: {str(e)}")
            return False

    def shutdown_all_instances(self):
        r"""关闭所有AI实例r"""
        try:
            for instance_id in list(self.instances.keys()):
                instance = self.instances[instance_id]
                instance.shutdown()
                del self.instances[instance_id]
            self.instance_counter = 0
            logger.info(r"所有AI实例已关闭")
        except Exception as e:
            logger.error(fr"关闭所有AI实例失败: {str(e)}")

    def get_instance_status(self, instance_id: str) -> Optional[Dict[str, Any]]:
        r"""获取AI实例状态r"""
        instance = self.instances.get(instance_id)
        if instance:
            return instance.get_status()
        return None

    def get_all_instance_statuses(self) -> Dict[str, Dict[str, Any]]:
        r"""获取所有AI实例状态r"""
        statuses = {}
        for instance_id, instance in self.instances.items():
            statuses[instance_id] = instance.get_status()
        return statuses


ai_instance_manager = AIInstanceManager()
