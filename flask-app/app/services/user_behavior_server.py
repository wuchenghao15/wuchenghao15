# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
用户行为子服务器模块 - 用于处理用户行为相关的任务
"""
import time
import threading
from app.utils.logging import logger
from app.services.distributed_server import distributed_server_manager
from app.ai.user_behavior_ai import get_user_behavior_ai
from app.utils.db import db_manager
import logging

class UserBehaviorServer:
    """用户行为子服务器类: 负责处理用户行为相关的任务"""

    def __init__(self, server_id=None):
        self.server_id = server_id or f"user_behavior_server_{int(time.time())}"
        self.is_running = False
        self.thread = None
        self.task_queue = []
        self.task_queue_lock = threading.Lock()
        self.heartbeat_interval = 15
        self.user_behavior_ai = get_user_behavior_ai()

    def start(self):
        """启动用户行为子服务器"""
        if self.is_running:
            logger.info(f"用户行为子服务器 {self.server_id} 已在运行")
            return

        logger.info(f"启动用户行为子服务器 {self.server_id}...")
        self.is_running = True

        self._register_to_manager()

        self.thread = threading.Thread(target=self._run_task_loop, daemon=True)
        self.thread.start()

        self.heartbeat_thread = threading.Thread(target=self._run_heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()

        logger.info(f"用户行为子服务器 {self.server_id} 启动成功")

    def stop(self):
        """停止用户行为子服务器"""
        if not self.is_running:
            logger.info(f"用户行为子服务器 {self.server_id} 未在运行")
            return

        logger.info(f"停止用户行为子服务器 {self.server_id}...")
        self.is_running = False

        if self.thread:
            self.thread.join(timeout=5)

        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=5)

        distributed_server_manager.remove_child_server(self.server_id)

        logger.info(f"用户行为子服务器 {self.server_id} 已停止")

    def _register_to_manager(self):
        """注册到分布式服务器管理器"""
        server_info = {
            'server_id': self.server_id,
            'ip': '127.0.0.1',
            'port': 0,
            'client_info': {
                'type': 'user_behavior_server',
                'version': '1.0.0',
                'capabilities': ['behavior_analysis', 'report_generation', 'anomaly_detection', 'behavior_prediction']
            },
            'load': 0,
            'resources': {
                'cpu_usage': 0,
                'memory_usage': 0,
                'disk_usage': 0,
                'network_traffic': 0,
                'response_time': 0
            }
        }

        success = distributed_server_manager.register_child_server(server_info)
        if success:
            logger.info(f"用户行为子服务器 {self.server_id} 注册成功")
        else:
            logger.error(f"用户行为子服务器 {self.server_id} 注册失败")

    def _run_heartbeat_loop(self):
        """心跳循环"""
        while self.is_running:
            try:
                distributed_server_manager.update_child_server_heartbeat(self.server_id)
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                logger.error(f"发送心跳失败: {str(e)}")
                time.sleep(5)

    def _run_task_loop(self):
        """任务处理循环"""
        while self.is_running:
            try:
                task = self._get_task()
                if task:
                    self._process_task(task)
                else:
                    time.sleep(1)
            except Exception as e:
                logger.error(f"任务处理循环发生错误: {str(e)}")
                time.sleep(5)

    def _get_task(self):
        """从队列中获取任务"""
        with self.task_queue_lock:
            if self.task_queue:
                return self.task_queue.pop(0)
            return None

    def _process_task(self, task):
        """处理任务"""
        task_type = task.get('task_type')
        task_data = task.get('task_data', {})
        
        if task_type == 'generate_behavior_report':
            return self._handle_generate_report(task_data)
        elif task_type == 'detect_anomalies':
            return self._handle_detect_anomalies(task_data)
        elif task_type == 'analyze_all_users_behavior':
            return self._handle_analyze_all_users(task_data)
        else:
            logger.warning(f"未知任务类型: {task_type}")
            return None

    def _handle_generate_report(self, task_data):
        """处理生成行为报告任务"""
        user_id = task_data.get('user_id')
        time_range = task_data.get('time_range', '7d')

        if not user_id:
            return {'success': False, 'error': '缺少用户ID'}
        
        return self.user_behavior_ai.generate_behavior_report(user_id, time_range)

    def _handle_detect_anomalies(self, task_data):
        """处理检测行为异常任务"""
        user_id = task_data.get('user_id')
        time_range = task_data.get('time_range', '24h')

        if not user_id:
            return {'success': False, 'error': '缺少用户ID'}
        
        return self.user_behavior_ai.detect_anomalies(user_id, time_range)

    def _handle_analyze_all_users(self, task_data):
        """处理分析所有用户行为任务"""
        time_range = task_data.get('time_range', '7d')
        return self.user_behavior_ai.analyze_all_users_behavior(time_range)

    def add_task(self, task):
        """添加任务到队列"""
        with self.task_queue_lock:
            self.task_queue.append(task)
            logger.info(f"任务已添加到队列: {task.get('task_id')}")

    def get_status(self):
        """获取服务器状态"""
        return {
            'server_id': self.server_id,
            'is_running': self.is_running,
            'queue_size': len(self.task_queue),
            'heartbeat_interval': self.heartbeat_interval,
            'ai_status': 'available' if self.user_behavior_ai else 'unavailable'
        }

_user_behavior_server = None

def get_user_behavior_server():
    """获取用户行为子服务器单例实例
    
    Returns:
        UserBehaviorServer: 用户行为子服务器实例
    """
    global _user_behavior_server
    if _user_behavior_server is None:
        try:
            _user_behavior_server = UserBehaviorServer()
        except Exception as e:
            logger.error(f"创建用户行为子服务器失败: {str(e)}")
            return None
    return _user_behavior_server

def start_user_behavior_server():
    """启动用户行为子服务器"""
    server = get_user_behavior_server()
    if server:
        server.start()
        return True
    return False

def stop_user_behavior_server():
    """停止用户行为子服务器"""
    server = get_user_behavior_server()
    if server:
        server.stop()
        return True
    return False

def assign_generate_report_task(user_id, time_range="7d"):
    """分配生成行为报告任务
    
    Args:
        user_id: 用户ID
        time_range: 时间范围
        
    Returns:
        dict: 任务分配结果
    """
    task_info = {
        'task_type': 'generate_behavior_report',
        'task_data': {
            'user_id': user_id,
            'time_range': time_range
        }
    }
    return distributed_server_manager.assign_task(task_info)

def assign_detect_anomalies_task(user_id, time_range="24h"):
    """分配检测行为异常任务
    
    Args:
        user_id: 用户ID
        time_range: 时间范围
        
    Returns:
        dict: 任务分配结果
    """
    task_info = {
        'task_type': 'detect_anomalies',
        'task_data': {
            'user_id': user_id,
            'time_range': time_range
        }
    }
    return distributed_server_manager.assign_task(task_info)

def assign_predict_behavior_task(user_id, time_range="7d"):
    """分配预测用户行为任务
    
    Args:
        user_id: 用户ID
        time_range: 时间范围
        
    Returns:
        dict: 任务分配结果
    """
    task_info = {
        'task_type': 'predict_user_behavior',
        'task_data': {
            'user_id': user_id,
            'time_range': time_range
        }
    }
    return distributed_server_manager.assign_task(task_info)

def assign_analyze_all_users_task(time_range="7d"):
    """分配分析所有用户行为任务
    
    Args:
        time_range: 时间范围
        
    Returns:
        dict: 任务分配结果
    """
    task_info = {
        'task_type': 'analyze_all_users_behavior',
        'task_data': {
            'time_range': time_range
        }
    }
    return distributed_server_manager.assign_task(task_info)
