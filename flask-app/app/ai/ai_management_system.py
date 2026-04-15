#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI管理系统
负责AI的整个生命周期管理，从创建、培训、部署到监控和回收
"""

import os
import json
import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# 导入其他模块
from app.ai.ai_capability_refiner import ai_capability_refiner
from app.ai.ai_training_monitor import ai_training_monitor
from app.ai.ai_instance_manager import ai_instance_manager
from app.ai.error_case_collector import error_case_collector
from app.ai.error_case_learner import error_case_learner

# 配置日志
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
        
        logger.info("AI管理系统初始化完成")
    
    def start(self):
        """启动AI管理系统"""
        try:
            self.running = True
            
            # 启动管理线程
            def management_loop():
                while self.running:
                    try:
                        # 检查AI实例状态
                        self._check_ai_instances()
                        
                        # 清理资源
                        self._cleanup_resources()
                        
                        # 睡眠一段时间
                        time.sleep(60)  # 每分钟检查一次
                    except Exception as e:
                        logger.error(f"管理线程错误: {str(e)}")
                        time.sleep(60)
            
            self.management_thread = threading.Thread(target=management_loop, daemon=True)
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
            
            # 等待管理线程结束
            if self.management_thread:
                self.management_thread.join(timeout=5)
            
            # 停止所有监控
            for ai_instance in self.ai_instances.values():
                ai_training_monitor.stop_monitoring(ai_instance.instance_id)
            
            logger.info("AI管理系统停止成功")
            return True
        except Exception as e:
            logger.error(f"停止AI管理系统失败: {str(e)}")
            return False
    
    def create_ai(self, instance_id: str, ai_type: str, capability: str = 'general') -> bool:
        """创建AI实例"""
        try:
            # 检查实例ID是否已存在
            if instance_id in self.ai_instances:
                logger.error(f"AI实例ID已存在: {instance_id}")
                return False
            
            # 检查能力是否存在
            if capability not in ai_capability_refiner.get_all_capabilities():
                logger.error(f"能力不存在: {capability}")
                return False
            
            # 创建AI实例
            from app.ai.base_ai import BaseAI
            ai_instance = BaseAI(instance_id, ai_type)
            
            # 细化AI能力
            if not ai_capability_refiner.refine_capability(ai_instance, capability):
                logger.error(f"细化AI能力失败: {capability}")
                return False
            
            # 注册AI实例
            if not ai_instance_manager.register_instance(ai_instance):
                logger.error(f"注册AI实例失败: {instance_id}")
                return False
            
            # 记录AI实例
            with self.lock:
                self.ai_instances[instance_id] = {
                    'instance': ai_instance,
                    'created_time': datetime.now().isoformat(),
                    'status': 'created',
                    'capability': capability
                }
                
                # 更新系统状态
                self.system_status['total_instances'] += 1
                self.system_status['last_updated'] = datetime.now().isoformat()
            
            logger.info(f"创建AI实例成功: {instance_id}, 能力: {capability}")
            return True
        except Exception as e:
            logger.error(f"创建AI实例失败: {str(e)}")
            return False
    
    def train_ai(self, instance_id: str) -> bool:
        """培训AI实例"""
        try:
            # 检查AI实例是否存在
            if instance_id not in self.ai_instances:
                logger.error(f"AI实例不存在: {instance_id}")
                return False
            
            ai_data = self.ai_instances[instance_id]
            ai_instance = ai_data['instance']
            
            # 检查AI实例是否已培训
            if hasattr(ai_instance, 'trained') and ai_instance.trained:
                logger.warning(f"AI实例 {instance_id} 已经培训过")
                return True
            
            # 培训AI实例
            if not ai_training_monitor.train_ai(ai_instance, ai_data['capability']):
                logger.error(f"培训AI实例失败: {instance_id}")
                return False
            
            # 更新AI实例状态
            with self.lock:
                self.ai_instances[instance_id]['status'] = 'trained'
                
                # 更新系统状态
                self.system_status['trained_instances'] += 1
                self.system_status['last_updated'] = datetime.now().isoformat()
            
            logger.info(f"培训AI实例成功: {instance_id}")
            return True
        except Exception as e:
            logger.error(f"培训AI实例失败: {str(e)}")
            return False
    
    def deploy_ai(self, instance_id: str, task: str) -> bool:
        """部署AI实例"""
        try:
            # 检查AI实例是否存在
            if instance_id not in self.ai_instances:
                logger.error(f"AI实例不存在: {instance_id}")
                return False
            
            ai_data = self.ai_instances[instance_id]
            ai_instance = ai_data['instance']
            
            # 检查AI实例是否已培训
            if not hasattr(ai_instance, 'trained') or not ai_instance.trained:
                logger.error(f"AI实例 {instance_id} 尚未培训")
                return False
            
            # 开始监控AI实例
            if not ai_training_monitor.start_monitoring(ai_instance):
                logger.error(f"开始监控AI实例失败: {instance_id}")
                return False
            
            # 分配任务
            with self.lock:
                self.ai_assignments[instance_id] = {
                    'task': task,
                    'assigned_time': datetime.now().isoformat(),
                    'status': 'active'
                }
                
                # 更新AI实例状态
                self.ai_instances[instance_id]['status'] = 'deployed'
                
                # 更新系统状态
                self.system_status['active_instances'] += 1
                self.system_status['monitoring_instances'] += 1
                self.system_status['last_updated'] = datetime.now().isoformat()
            
            logger.info(f"部署AI实例成功: {instance_id}, 任务: {task}")
            return True
        except Exception as e:
            logger.error(f"部署AI实例失败: {str(e)}")
            return False
    
    def recycle_ai(self, instance_id: str) -> bool:
        """回收AI实例"""
        try:
            # 检查AI实例是否存在
            if instance_id not in self.ai_instances:
                logger.error(f"AI实例不存在: {instance_id}")
                return False
            
            ai_data = self.ai_instances[instance_id]
            ai_instance = ai_data['instance']
            
            # 回收AI实例
            if not ai_training_monitor.recycle_ai(ai_instance):
                logger.error(f"回收AI实例失败: {instance_id}")
                return False
            
            # 注销AI实例
            if not ai_instance_manager.unregister_instance(instance_id):
                logger.error(f"注销AI实例失败: {instance_id}")
                return False
            
            # 更新系统状态
            with self.lock:
                # 移除AI实例
                del self.ai_instances[instance_id]
                
                # 移除任务分配
                if instance_id in self.ai_assignments:
                    del self.ai_assignments[instance_id]
                
                # 更新系统状态
                self.system_status['total_instances'] -= 1
                if ai_data['status'] == 'deployed':
                    self.system_status['active_instances'] -= 1
                    self.system_status['monitoring_instances'] -= 1
                if hasattr(ai_instance, 'trained') and ai_instance.trained:
                    self.system_status['trained_instances'] -= 1
                
                self.system_status['last_updated'] = datetime.now().isoformat()
            
            logger.info(f"回收AI实例成功: {instance_id}")
            return True
        except Exception as e:
            logger.error(f"回收AI实例失败: {str(e)}")
            return False
    
    def get_ai_status(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """获取AI实例状态"""
        try:
            if instance_id not in self.ai_instances:
                return None
            
            ai_data = self.ai_instances[instance_id]
            ai_instance = ai_data['instance']
            
            # 获取基本状态
            status = {
                'instance_id': instance_id,
                'status': ai_data['status'],
                'capability': ai_data['capability'],
                'created_time': ai_data['created_time'],
                'trained': hasattr(ai_instance, 'trained') and ai_instance.trained,
                'training_history': ai_instance.training_history if hasattr(ai_instance, 'training_history') else [],
                'refinement_history': ai_instance.refinement_history if hasattr(ai_instance, 'refinement_history') else []
            }
            
            # 获取监控数据
            monitoring_data = ai_training_monitor.get_monitoring_data(instance_id)
            if monitoring_data:
                status['monitoring_data'] = monitoring_data
            
            # 获取任务分配
            if instance_id in self.ai_assignments:
                status['assignment'] = self.ai_assignments[instance_id]
            
            return status
        except Exception as e:
            logger.error(f"获取AI实例状态失败: {str(e)}")
            return None
    
    def get_all_ai_statuses(self) -> Dict[str, Dict[str, Any]]:
        """获取所有AI实例状态"""
        try:
            statuses = {}
            for instance_id in self.ai_instances:
                status = self.get_ai_status(instance_id)
                if status:
                    statuses[instance_id] = status
            return statuses
        except Exception as e:
            logger.error(f"获取所有AI实例状态失败: {str(e)}")
            return {}
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            with self.lock:
                return self.system_status.copy()
        except Exception as e:
            logger.error(f"获取系统状态失败: {str(e)}")
            return {}
    
    def _check_ai_instances(self):
        """检查AI实例状态"""
        try:
            for instance_id, ai_data in list(self.ai_instances.items()):
                ai_instance = ai_data['instance']
                
                # 检查AI实例是否有错误
                if hasattr(ai_instance, 'get_status'):
                    status = ai_instance.get_status()
                    if status and status.get('status') == 'error':
                        # 处理AI错误
                        error_message = status.get('error', 'Unknown error')
                        error_case_collector.capture_exception(Exception(error_message), {
                            'ai_instance_id': instance_id,
                            'ai_capability': ai_data['capability'],
                            'error_message': error_message
                        })
                        
                        # 尝试自动修复
                        if hasattr(ai_instance, 'recover'):
                            ai_instance.recover()
        except Exception as e:
            logger.error(f"检查AI实例状态失败: {str(e)}")
    
    def _cleanup_resources(self):
        """清理资源"""
        try:
            # 检查长时间未活动的AI实例
            current_time = datetime.now().timestamp()
            for instance_id, ai_data in list(self.ai_instances.items()):
                # 检查是否超过30分钟未活动
                if ai_data['status'] == 'deployed' and instance_id in self.ai_assignments:
                    assignment_time = datetime.fromisoformat(self.ai_assignments[instance_id]['assigned_time']).timestamp()
                    if current_time - assignment_time > 30 * 60:  # 30分钟
                        # 回收长时间未活动的AI实例
                        logger.info(f"回收长时间未活动的AI实例: {instance_id}")
                        self.recycle_ai(instance_id)
        except Exception as e:
            logger.error(f"清理资源失败: {str(e)}")
    
    def auto_scale(self):
        """自动扩缩容"""
        try:
            # 基于系统负载自动调整AI实例数量
            # 这里可以根据实际需求实现
            pass
        except Exception as e:
            logger.error(f"自动扩缩容失败: {str(e)}")

# 创建全局AI管理系统实例
ai_management_system = AIManagementSystem()

if __name__ == '__main__':
    print("AI管理系统初始化成功")
    
    # 启动系统
    ai_management_system.start()
    
    # 测试创建AI实例
    print("\n测试创建AI实例...")
    success = ai_management_system.create_ai('test-ai-1', 'general', 'engineering')
    print(f"创建结果: {'成功' if success else '失败'}")
    
    # 测试培训AI实例
    print("\n测试培训AI实例...")
    success = ai_management_system.train_ai('test-ai-1')
    print(f"培训结果: {'成功' if success else '失败'}")
    
    # 测试部署AI实例
    print("\n测试部署AI实例...")
    success = ai_management_system.deploy_ai('test-ai-1', '分析代码性能问题')
    print(f"部署结果: {'成功' if success else '失败'}")
    
    # 等待一段时间
    print("\n等待10秒...")
    time.sleep(10)
    
    # 测试获取AI实例状态
    print("\n测试获取AI实例状态...")
    status = ai_management_system.get_ai_status('test-ai-1')
    print(f"AI实例状态: {status}")
    
    # 测试获取系统状态
    print("\n测试获取系统状态...")
    system_status = ai_management_system.get_system_status()
    print(f"系统状态: {system_status}")
    
    # 测试回收AI实例
    print("\n测试回收AI实例...")
    success = ai_management_system.recycle_ai('test-ai-1')
    print(f"回收结果: {'成功' if success else '失败'}")
    
    # 停止系统
    ai_management_system.stop()
    print("\nAI管理系统停止成功")
