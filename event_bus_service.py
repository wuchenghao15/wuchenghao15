#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS事件总线服务
提供事件驱动架构支持
"""

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable

logger = print

class Event:
    """事件"""
    
    def __init__(self, event_id: str, event_type: str,
                 payload: Dict[str, Any] = None,
                 source: str = '', timestamp: float = None,
                 metadata: Dict[str, Any] = None):
        self.event_id = event_id
        self.event_type = event_type
        self.payload = payload or {}
        self.source = source
        self.timestamp = timestamp or time.time()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'payload': self.payload,
            'source': self.source,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }

class EventHandler:
    """事件处理器"""
    
    def __init__(self, handler_id: str, event_type: str,
                 callback: Callable, priority: int = 100,
                 filter_func: Callable = None, enabled: bool = True):
        self.handler_id = handler_id
        self.event_type = event_type
        self.callback = callback
        self.priority = priority
        self.filter_func = filter_func
        self.enabled = enabled
        self.call_count = 0
        self.last_call = None
    
    def handle(self, event: Event):
        """处理事件"""
        if not self.enabled:
            return
        
        if self.filter_func and not self.filter_func(event):
            return
        
        try:
            self.callback(event)
            self.call_count += 1
            self.last_call = datetime.now().isoformat()
        except Exception as e:
            logger(f"[事件] 处理器 {self.handler_id} 处理事件失败: {e}")

class EventBusService:
    """事件总线服务"""
    
    def __init__(self):
        self.handlers: Dict[str, List[EventHandler]] = {}
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_queue: List[Event] = []
        self.is_running = False
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    event_type TEXT NOT NULL,
                    payload TEXT,
                    source TEXT,
                    timestamp REAL,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS event_handlers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    handler_id TEXT NOT NULL UNIQUE,
                    event_type TEXT NOT NULL,
                    name TEXT,
                    priority INTEGER DEFAULT 100,
                    enabled INTEGER DEFAULT 1,
                    call_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS event_delivery_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    handler_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    delivered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    error_message TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_events_id ON events(event_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_event_handlers_type ON event_handlers(event_type)
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[事件] 初始化数据库失败: {e}")
    
    def _generate_event_id(self) -> str:
        """生成事件ID"""
        import uuid
        return str(uuid.uuid4())
    
    def _generate_handler_id(self) -> str:
        """生成处理器ID"""
        return f"handler_{int(time.time())}_{hash(os.urandom(16))}"
    
    def publish(self, event_type: str, payload: Dict[str, Any] = None,
                source: str = '', metadata: Dict[str, Any] = None):
        """发布事件"""
        event = Event(
            event_id=self._generate_event_id(),
            event_type=event_type,
            payload=payload or {},
            source=source,
            metadata=metadata or {}
        )
        
        self._save_event_to_db(event)
        self._dispatch_event(event)
        
        logger(f"[事件] 发布事件: {event_type} - {event.event_id}")
    
    def _save_event_to_db(self, event: Event):
        """保存事件到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO events 
                (event_id, event_type, payload, source, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                event.event_id, event.event_type,
                json.dumps(event.payload), event.source,
                event.timestamp, json.dumps(event.metadata)
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[事件] 保存事件失败: {e}")
    
    def _dispatch_event(self, event: Event):
        """分发事件"""
        handlers = self.handlers.get(event.event_type, [])
        
        handlers.sort(key=lambda h: h.priority)
        
        for handler in handlers:
            thread = threading.Thread(target=handler.handle, args=(event,), daemon=True)
            thread.start()
    
    def subscribe(self, event_type: str, callback: Callable,
                  priority: int = 100, filter_func: Callable = None,
                  name: str = '') -> str:
        """订阅事件"""
        handler_id = self._generate_handler_id()
        
        handler = EventHandler(
            handler_id=handler_id,
            event_type=event_type,
            callback=callback,
            priority=priority,
            filter_func=filter_func,
            enabled=True
        )
        
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        self.handlers[event_type].append(handler)
        
        self._save_handler_to_db(handler_id, event_type, name, priority)
        
        logger(f"[事件] 订阅事件: {event_type} - {name}")
        
        return handler_id
    
    def _save_handler_to_db(self, handler_id: str, event_type: str,
                            name: str, priority: int):
        """保存处理器到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO event_handlers 
                (handler_id, event_type, name, priority, enabled)
                VALUES (?, ?, ?, ?, ?)
            ''', (handler_id, event_type, name or '', priority, 1))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[事件] 保存处理器失败: {e}")
    
    def unsubscribe(self, handler_id: str) -> bool:
        """取消订阅"""
        for event_type, handlers in self.handlers.items():
            for i, handler in enumerate(handlers):
                if handler.handler_id == handler_id:
                    handlers.pop(i)
                    if not handlers:
                        del self.handlers[event_type]
                    logger(f"[事件] 取消订阅: {handler_id}")
                    return True
        
        logger(f"[事件] 处理器不存在: {handler_id}")
        return False
    
    def register_handler(self, event_type: str, name: str = '',
                        priority: int = 100, filter_func: Callable = None):
        """装饰器：注册事件处理器"""
        def decorator(func: Callable):
            self.subscribe(event_type, func, priority, filter_func, name)
            return func
        return decorator
    
    def publish_sync(self, event_type: str, payload: Dict[str, Any] = None,
                     source: str = '', metadata: Dict[str, Any] = None):
        """同步发布事件"""
        event = Event(
            event_id=self._generate_event_id(),
            event_type=event_type,
            payload=payload or {},
            source=source,
            metadata=metadata or {}
        )
        
        self._save_event_to_db(event)
        
        handlers = self.handlers.get(event_type, [])
        handlers.sort(key=lambda h: h.priority)
        
        for handler in handlers:
            handler.handle(event)
        
        logger(f"[事件] 同步发布事件: {event_type}")
    
    def get_events(self, event_type: str = None, limit: int = 100,
                   since: float = None) -> List[Event]:
        """获取事件列表"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            query = 'SELECT * FROM events WHERE 1=1'
            params = []
            
            if event_type:
                query += ' AND event_type = ?'
                params.append(event_type)
            
            if since:
                query += ' AND timestamp >= ?'
                params.append(since)
            
            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            
            columns = [desc[0] for desc in cursor.description]
            events = []
            
            for row in cursor.fetchall():
                data = dict(zip(columns, row))
                event = Event(
                    event_id=data['event_id'],
                    event_type=data['event_type'],
                    payload=json.loads(data['payload'] or '{}'),
                    source=data['source'],
                    timestamp=data['timestamp'],
                    metadata=json.loads(data['metadata'] or '{}')
                )
                events.append(event)
            
            conn.close()
            return events
        except Exception as e:
            logger(f"[事件] 获取事件失败: {e}")
            return []
    
    def get_handlers(self, event_type: str = None) -> List[EventHandler]:
        """获取处理器列表"""
        all_handlers = []
        
        for etype, handlers in self.handlers.items():
            if event_type is None or etype == event_type:
                all_handlers.extend(handlers)
        
        return all_handlers
    
    def get_event_types(self) -> List[str]:
        """获取所有事件类型"""
        return list(self.handlers.keys())
    
    def get_event_stats(self, event_type: str = None) -> Dict[str, Any]:
        """获取事件统计"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            query = 'SELECT event_type, COUNT(*) as count FROM events WHERE 1=1'
            params = []
            
            if event_type:
                query += ' AND event_type = ?'
                params.append(event_type)
            
            query += ' GROUP BY event_type ORDER BY count DESC'
            
            cursor.execute(query, params)
            
            stats = {}
            
            for row in cursor.fetchall():
                stats[row[0]] = row[1]
            
            conn.close()
            
            return stats
        except Exception as e:
            logger(f"[事件] 获取统计失败: {e}")
            return {}
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        total_handlers = sum(len(handlers) for handlers in self.handlers.values())
        
        return {
            'status': 'running' if self.is_running else 'stopped',
            'total_event_types': len(self.handlers),
            'total_handlers': total_handlers,
            'event_types': list(self.handlers.keys())
        }
    
    def start(self):
        """启动事件总线服务"""
        if self.is_running:
            return
        
        self.is_running = True
        logger(f"[事件] 事件总线服务已启动")
    
    def stop(self):
        """停止事件总线服务"""
        self.is_running = False
        logger(f"[事件] 事件总线服务已停止")

event_bus_service = EventBusService()
