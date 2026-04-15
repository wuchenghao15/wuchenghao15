#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI实例管理器模块
负责管理AI实例的生命周期
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# 配置日志
logger = logging.getLogger('ai_instance_manager')

class AIInstanceManager:
    """AI实例管理器类"""
    
    def __init__(self):
        """初始化AI实例管理器"""
        self.instances = {}
        self.instance_counter = 0
        logger.info("AI实例管理器初始化完成")
    
    def register_instance(self, ai_instance: Any) -> bool:
        """注册AI实例"""
        try:
            instance_id = ai_instance.instance_id
            if instance_id not in self.instances:
                self.instances[instance_id] = ai_instance
                self.instance_counter += 1
                logger.info(f"AI实例注册成功: {instance_id}")
            else:
                logger.warning(f"AI实例已存在: {instance_id}")
            return True
        except Exception as e:
            logger.error(f"注册AI实例失败: {str(e)}")
            return False
    
    def unregister_instance(self, instance_id: str) -> bool:
        """注销AI实例"""
        try:
            if instance_id in self.instances:
                # 关闭AI实例
                self.instances[instance_id].shutdown()
                # 从实例列表中移除
                del self.instances[instance_id]
                self.instance_counter -= 1
                logger.info(f"AI实例注销成功: {instance_id}")
            else:
                logger.warning(f"AI实例不存在: {instance_id}")
            return True
        except Exception as e:
            logger.error(f"注销AI实例失败: {str(e)}")
            return False
    
    def get_instance(self, instance_id: str) -> Optional[Any]:
        """获取AI实例"""
        return self.instances.get(instance_id)
    
    def get_instances_by_type(self, ai_type: str) -> List[Any]:
        """按类型获取AI实例"""
        return [instance for instance in self.instances.values() if instance.ai_type == ai_type]
    
    def get_all_instances(self) -> List[Any]:
        """获取所有AI实例"""
        return list(self.instances.values())
    
    def get_instance_count(self) -> int:
        """获取AI实例数量"""
        return self.instance_counter
    
    def shutdown_all_instances(self):
        """关闭所有AI实例"""
        try:
            for instance_id, instance in list(self.instances.items()):
                instance.shutdown()
                del self.instances[instance_id]
            self.instance_counter = 0
            logger.info("所有AI实例已关闭")
        except Exception as e:
            logger.error(f"关闭所有AI实例失败: {str(e)}")
    
    def get_instance_status(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """获取AI实例状态"""
        instance = self.get_instance(instance_id)
        if instance:
            return instance.get_status()
        return None
    
    def get_all_instance_statuses(self) -> Dict[str, Dict[str, Any]]:
        """获取所有AI实例状态"""
        statuses = {}
        for instance_id, instance in self.instances.items():
            statuses[instance_id] = instance.get_status()
        return statuses

# 创建全局AI实例管理器实例
ai_instance_manager = AIInstanceManager()

if __name__ == '__main__':
    # 测试AI实例管理器
    from app.ai.base_ai import BaseAI
    
    # 创建测试AI实例
    test_ai1 = BaseAI('test-ai-1', 'test')
    test_ai2 = BaseAI('test-ai-2', 'test')
    test_ai3 = BaseAI('test-ai-3', 'production')
    
    # 注册AI实例
    print("注册AI实例:")
    ai_instance_manager.register_instance(test_ai1)
    ai_instance_manager.register_instance(test_ai2)
    ai_instance_manager.register_instance(test_ai3)
    
    # 获取实例数量
    print(f"\nAI实例数量: {ai_instance_manager.get_instance_count()}")
    
    # 按类型获取实例
    print("\n按类型获取实例:")
    test_instances = ai_instance_manager.get_instances_by_type('test')
    print(f"测试类型实例数量: {len(test_instances)}")
    for instance in test_instances:
        print(f"- {instance.instance_id}")
    
    # 获取所有实例
    print("\n所有AI实例:")
    all_instances = ai_instance_manager.get_all_instances()
    for instance in all_instances:
        print(f"- {instance.instance_id} (类型: {instance.ai_type})")
    
    # 获取实例状态
    print("\n获取实例状态:")
    status = ai_instance_manager.get_instance_status('test-ai-1')
    if status:
        print(f"test-ai-1 状态: {status['status']}")
    
    # 获取所有实例状态
    print("\n所有实例状态:")
    all_statuses = ai_instance_manager.get_all_instance_statuses()
    for instance_id, status in all_statuses.items():
        print(f"{instance_id}: {status['status']}")
    
    # 注销实例
    print("\n注销AI实例:")
    ai_instance_manager.unregister_instance('test-ai-1')
    print(f"AI实例数量: {ai_instance_manager.get_instance_count()}")
    
    # 关闭所有实例
    print("\n关闭所有AI实例:")
    ai_instance_manager.shutdown_all_instances()
    print(f"AI实例数量: {ai_instance_manager.get_instance_count()}")