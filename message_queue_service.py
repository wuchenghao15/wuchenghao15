#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS消息队列服务
提供异步任务处理和消息传递功能
"""

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable

logger = print

class Message:
    """消息"""
    
    def __init__(self, message_id: str, queue_name: str, body: Dict[str, Any],
                 priority: str = 'normal', retry_count: int = 0,
                 max_retries: int = 3, created_at: str = None):
        self.message_id = message_id
        self.queue_name = queue_name
        self.body = body
        self.priority = priority
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.created_at = created_at or datetime.now().isoformat()
        self.status = 'pending'
        self.processed_at = None
        self.error_message = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'message_id': self.message_id,
            'queue_name': self.queue_name,
            'body': self.body,
            'priority': self.priority,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'created_at': self.created_at,
            'status': self.status,
            'processed_at': self.processed_at,
            'error_message': self.error_message
        }

class MessageQueue:
    """消息队列"""
    
    def __init__(self, queue_name: str, max_size: int = 10000,
                 retention_days: int = 7):
        self.queue_name = queue_name
        self.max_size = max_size
        self.retention_days = retention_days
        self.messages: List[Message] = []
        self.processors: List[Callable] = []
        self.is_running = False
        self.processing_thread = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'queue_name': self.queue_name,
            'message_count': len(self.messages),
            'max_size': self.max_size,
            'retention_days': self.retention_days,
            'processor_count': len(self.processors),
            'is_running': self.is_running
        }

class MessageQueueService:
    """消息队列服务"""
    
    def __init__(self):
        self.queues: Dict[str, MessageQueue] = {}
        self.is_running = False
        self.lock = threading.Lock()
        
        self.config = self._load_config()
        self._init_database()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'mq_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'default_max_size': 10000,
            'default_retention_days': 7,
            'process_interval': 1,
            'max_concurrent_processors': 10,
            'enable_persistence': True
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'mq_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS message_queues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    queue_name TEXT NOT NULL UNIQUE,
                    max_size INTEGER DEFAULT 10000,
                    retention_days INTEGER DEFAULT 7,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT NOT NULL UNIQUE,
                    queue_name TEXT NOT NULL,
                    body TEXT NOT NULL,
                    priority TEXT DEFAULT 'normal',
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    processed_at TEXT,
                    error_message TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_messages_queue ON messages(queue_name)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status)
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[队列] 初始化数据库失败: {e}")
    
    def _generate_message_id(self) -> str:
        """生成消息ID"""
        return f"msg_{int(time.time())}_{hash(os.urandom(16))}"
    
    def create_queue(self, queue_name: str, max_size: int = None,
                     retention_days: int = None) -> bool:
        """创建队列"""
        if queue_name in self.queues:
            logger(f"[队列] 队列已存在: {queue_name}")
            return False
        
        max_size = max_size or self.config['default_max_size']
        retention_days = retention_days or self.config['default_retention_days']
        
        queue = MessageQueue(queue_name, max_size, retention_days)
        
        with self.lock:
            self.queues[queue_name] = queue
        
        self._save_queue_to_db(queue)
        logger(f"[队列] 创建队列: {queue_name}")
        
        return True
    
    def _save_queue_to_db(self, queue: MessageQueue):
        """保存队列到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO message_queues (queue_name, max_size, retention_days)
                VALUES (?, ?, ?)
            ''', (queue.queue_name, queue.max_size, queue.retention_days))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[队列] 保存队列失败: {e}")
    
    def delete_queue(self, queue_name: str) -> bool:
        """删除队列"""
        with self.lock:
            if queue_name not in self.queues:
                logger(f"[队列] 队列不存在: {queue_name}")
                return False
            
            queue = self.queues[queue_name]
            
            if queue.is_running:
                queue.is_running = False
                if queue.processing_thread:
                    queue.processing_thread.join()
            
            del self.queues[queue_name]
        
        self._delete_queue_from_db(queue_name)
        logger(f"[队列] 删除队列: {queue_name}")
        
        return True
    
    def _delete_queue_from_db(self, queue_name: str):
        """从数据库删除队列"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM message_queues WHERE queue_name = ?', (queue_name,))
            cursor.execute('DELETE FROM messages WHERE queue_name = ?', (queue_name,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[队列] 删除队列失败: {e}")
    
    def enqueue(self, queue_name: str, body: Dict[str, Any],
                priority: str = 'normal', max_retries: int = 3) -> str:
        """入队"""
        with self.lock:
            if queue_name not in self.queues:
                self.create_queue(queue_name)
            
            queue = self.queues[queue_name]
            
            if len(queue.messages) >= queue.max_size:
                logger(f"[队列] 队列已满: {queue_name}")
                return ''
            
            message_id = self._generate_message_id()
            
            message = Message(
                message_id=message_id,
                queue_name=queue_name,
                body=body,
                priority=priority,
                max_retries=max_retries
            )
            
            queue.messages.append(message)
            queue.messages.sort(key=self._priority_key)
        
        self._save_message_to_db(message)
        logger(f"[队列] 消息入队: {message_id}")
        
        if not queue.is_running and queue.processors:
            self._start_queue_processing(queue)
        
        return message_id
    
    def _priority_key(self, message: Message) -> int:
        """优先级排序键"""
        priority_order = {'high': 0, 'normal': 1, 'low': 2}
        return priority_order.get(message.priority, 1)
    
    def _save_message_to_db(self, message: Message):
        """保存消息到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO messages 
                (message_id, queue_name, body, priority, retry_count, max_retries, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                message.message_id, message.queue_name,
                json.dumps(message.body),
                message.priority, message.retry_count,
                message.max_retries, message.status,
                message.created_at
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[队列] 保存消息失败: {e}")
    
    def dequeue(self, queue_name: str) -> Optional[Message]:
        """出队"""
        with self.lock:
            if queue_name not in self.queues:
                return None
            
            queue = self.queues[queue_name]
            
            if not queue.messages:
                return None
            
            message = queue.messages.pop(0)
            message.status = 'processing'
        
        self._update_message_status(message.message_id, 'processing')
        return message
    
    def _update_message_status(self, message_id: str, status: str):
        """更新消息状态"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('UPDATE messages SET status = ? WHERE message_id = ?',
                          (status, message_id))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[队列] 更新消息状态失败: {e}")
    
    def acknowledge(self, message_id: str):
        """确认消息处理完成"""
        with self.lock:
            for queue in self.queues.values():
                for message in queue.messages:
                    if message.message_id == message_id:
                        message.status = 'completed'
                        message.processed_at = datetime.now().isoformat()
                        break
        
        self._complete_message(message_id)
        logger(f"[队列] 消息确认: {message_id}")
    
    def _complete_message(self, message_id: str):
        """完成消息"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE messages 
                SET status = 'completed', processed_at = ?
                WHERE message_id = ?
            ''', (datetime.now().isoformat(), message_id))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[队列] 完成消息失败: {e}")
    
    def reject(self, message_id: str, requeue: bool = True):
        """拒绝消息"""
        with self.lock:
            for queue in self.queues.values():
                for message in queue.messages:
                    if message.message_id == message_id:
                        message.status = 'failed'
                        message.retry_count += 1
                        
                        if requeue and message.retry_count < message.max_retries:
                            message.status = 'pending'
                            queue.messages.append(message)
                            queue.messages.sort(key=self._priority_key)
                            
                            logger(f"[队列] 消息重新入队: {message_id}")
                        else:
                            logger(f"[队列] 消息拒绝: {message_id}")
                        break
        
        self._update_message_status(message_id, 'failed')
    
    def subscribe(self, queue_name: str, processor: Callable):
        """订阅队列"""
        with self.lock:
            if queue_name not in self.queues:
                self.create_queue(queue_name)
            
            queue = self.queues[queue_name]
            queue.processors.append(processor)
            
            if not queue.is_running:
                self._start_queue_processing(queue)
        
        logger(f"[队列] 订阅队列: {queue_name}")
    
    def _start_queue_processing(self, queue: MessageQueue):
        """启动队列处理"""
        queue.is_running = True
        
        def process_loop():
            while queue.is_running:
                try:
                    message = self.dequeue(queue.queue_name)
                    
                    if message:
                        for processor in queue.processors:
                            try:
                                processor(message.body)
                            except Exception as e:
                                logger(f"[队列] 消息处理失败: {e}")
                                self.reject(message.message_id)
                                break
                        else:
                            self.acknowledge(message.message_id)
                    
                    time.sleep(self.config['process_interval'])
                except Exception as e:
                    logger(f"[队列] 处理循环错误: {e}")
        
        queue.processing_thread = threading.Thread(target=process_loop, daemon=True)
        queue.processing_thread.start()
    
    def unsubscribe(self, queue_name: str, processor: Callable):
        """取消订阅"""
        with self.lock:
            if queue_name not in self.queues:
                return
            
            queue = self.queues[queue_name]
            
            if processor in queue.processors:
                queue.processors.remove(processor)
            
            if not queue.processors and queue.is_running:
                queue.is_running = False
                if queue.processing_thread:
                    queue.processing_thread.join()
        
        logger(f"[队列] 取消订阅: {queue_name}")
    
    def get_queue(self, queue_name: str) -> Optional[MessageQueue]:
        """获取队列"""
        return self.queues.get(queue_name)
    
    def get_queues(self) -> List[MessageQueue]:
        """获取所有队列"""
        with self.lock:
            return list(self.queues.values())
    
    def get_queue_stats(self, queue_name: str) -> Dict[str, Any]:
        """获取队列统计"""
        with self.lock:
            queue = self.queues.get(queue_name)
            
            if not queue:
                return {'error': '队列不存在'}
            
            pending = sum(1 for m in queue.messages if m.status == 'pending')
            processing = sum(1 for m in queue.messages if m.status == 'processing')
            completed = sum(1 for m in queue.messages if m.status == 'completed')
            failed = sum(1 for m in queue.messages if m.status == 'failed')
            
            return {
                'queue_name': queue.queue_name,
                'total_messages': len(queue.messages),
                'pending_messages': pending,
                'processing_messages': processing,
                'completed_messages': completed,
                'failed_messages': failed,
                'max_size': queue.max_size,
                'retention_days': queue.retention_days,
                'processor_count': len(queue.processors),
                'is_running': queue.is_running
            }
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        with self.lock:
            total_messages = sum(len(q.messages) for q in self.queues.values())
            running_queues = sum(1 for q in self.queues.values() if q.is_running)
            
            return {
                'status': 'running' if self.is_running else 'stopped',
                'total_queues': len(self.queues),
                'total_messages': total_messages,
                'running_queues': running_queues,
                'process_interval': self.config['process_interval'],
                'max_concurrent_processors': self.config['max_concurrent_processors'],
                'enable_persistence': self.config['enable_persistence']
            }
    
    def start(self):
        """启动消息队列服务"""
        if self.is_running:
            return
        
        self.is_running = True
        
        for queue in self.queues.values():
            if queue.processors and not queue.is_running:
                self._start_queue_processing(queue)
        
        logger(f"[队列] 消息队列服务已启动")
    
    def stop(self):
        """停止消息队列服务"""
        self.is_running = False
        
        for queue in self.queues.values():
            if queue.is_running:
                queue.is_running = False
                if queue.processing_thread:
                    queue.processing_thread.join()
        
        logger(f"[队列] 消息队列服务已停止")

mq_service = MessageQueueService()
