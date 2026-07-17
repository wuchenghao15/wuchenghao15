#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS分布式ID生成服务
提供全局唯一ID生成功能
"""

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional

logger = print

class IDGenerator:
    """ID生成器"""
    
    def __init__(self, generator_id: str, name: str,
                 generator_type: str = 'snowflake',
                 worker_id: int = 0, datacenter_id: int = 0,
                 sequence: int = 0):
        self.generator_id = generator_id
        self.name = name
        self.generator_type = generator_type
        self.worker_id = worker_id
        self.datacenter_id = datacenter_id
        self.sequence = sequence
        self.last_timestamp = -1
        self.lock = threading.Lock()
    
    def generate(self) -> str:
        """生成ID"""
        if self.generator_type == 'snowflake':
            return self._generate_snowflake()
        elif self.generator_type == 'uuid':
            return self._generate_uuid()
        elif self.generator_type == 'timestamp':
            return self._generate_timestamp()
        elif self.generator_type == 'hash':
            return self._generate_hash()
        else:
            return self._generate_snowflake()
    
    def _generate_snowflake(self) -> str:
        """生成雪花算法ID"""
        twepoch = 1420041600000
        
        with self.lock:
            timestamp = int(time.time() * 1000)
            
            if timestamp < self.last_timestamp:
                raise Exception(f"时钟回拨: {timestamp} < {self.last_timestamp}")
            
            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & 4095
                if self.sequence == 0:
                    timestamp = self._wait_next_millisecond(timestamp)
            else:
                self.sequence = 0
            
            self.last_timestamp = timestamp
            
            id_value = ((timestamp - twepoch) << 22) | \
                       (self.datacenter_id << 17) | \
                       (self.worker_id << 12) | \
                       self.sequence
            
            return str(id_value)
    
    def _wait_next_millisecond(self, timestamp: int) -> int:
        """等待下一毫秒"""
        while timestamp <= self.last_timestamp:
            timestamp = int(time.time() * 1000)
        return timestamp
    
    def _generate_uuid(self) -> str:
        """生成UUID"""
        import uuid
        return str(uuid.uuid4())
    
    def _generate_timestamp(self) -> str:
        """生成时间戳ID"""
        return str(int(time.time() * 1000000)) + str(self.sequence).zfill(4)
    
    def _generate_hash(self) -> str:
        """生成哈希ID"""
        import hashlib
        data = f"{time.time()}_{os.urandom(16)}_{self.sequence}"
        return hashlib.md5(data.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'generator_id': self.generator_id,
            'name': self.name,
            'generator_type': self.generator_type,
            'worker_id': self.worker_id,
            'datacenter_id': self.datacenter_id,
            'sequence': self.sequence,
            'last_timestamp': self.last_timestamp
        }

class DistributedIDService:
    """分布式ID生成服务"""
    
    def __init__(self):
        self.generators: Dict[str, IDGenerator] = {}
        self.id_counters: Dict[str, int] = {}
        self.is_running = False
        self.lock = threading.Lock()
        
        self._init_database()
        self._register_default_generators()
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS id_generators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    generator_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    generator_type TEXT DEFAULT 'snowflake',
                    worker_id INTEGER DEFAULT 0,
                    datacenter_id INTEGER DEFAULT 0,
                    sequence INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS id_counters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    counter_name TEXT NOT NULL UNIQUE,
                    current_value INTEGER DEFAULT 0,
                    step INTEGER DEFAULT 1,
                    min_value INTEGER DEFAULT 0,
                    max_value INTEGER DEFAULT 999999999,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS id_generation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    generator_id TEXT NOT NULL,
                    generated_id TEXT NOT NULL,
                    generated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_id_generators_id ON id_generators(generator_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_id_counters_name ON id_counters(counter_name)
            ''')
            
            conn.commit()
            conn.close()
            
            self._load_counters_from_db()
        except Exception as e:
            logger(f"[ID] 初始化数据库失败: {e}")
    
    def _load_counters_from_db(self):
        """从数据库加载计数器"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT counter_name, current_value FROM id_counters')
            
            for row in cursor.fetchall():
                self.id_counters[row[0]] = row[1]
            
            conn.close()
        except Exception as e:
            logger(f"[ID] 加载计数器失败: {e}")
    
    def _register_default_generators(self):
        """注册默认ID生成器"""
        default_generators = [
            IDGenerator('snowflake_default', '默认雪花ID', 'snowflake', 1, 1),
            IDGenerator('uuid_default', '默认UUID', 'uuid'),
            IDGenerator('timestamp_default', '默认时间戳', 'timestamp'),
            IDGenerator('hash_default', '默认哈希', 'hash'),
            IDGenerator('user_id', '用户ID', 'snowflake', 1, 1),
            IDGenerator('order_id', '订单ID', 'snowflake', 2, 1),
            IDGenerator('transaction_id', '交易ID', 'snowflake', 3, 1),
            IDGenerator('log_id', '日志ID', 'uuid'),
            IDGenerator('trace_id', '追踪ID', 'uuid'),
            IDGenerator('request_id', '请求ID', 'uuid')
        ]
        
        for generator in default_generators:
            if generator.generator_id not in self.generators:
                self.generators[generator.generator_id] = generator
                self._save_generator_to_db(generator)
    
    def _generate_generator_id(self) -> str:
        """生成生成器ID"""
        return f"gen_{int(time.time())}_{hash(os.urandom(16))}"
    
    def add_generator(self, name: str, generator_type: str = 'snowflake',
                      worker_id: int = 0, datacenter_id: int = 0) -> str:
        """添加ID生成器"""
        generator_id = self._generate_generator_id()
        
        generator = IDGenerator(
            generator_id=generator_id,
            name=name,
            generator_type=generator_type,
            worker_id=worker_id,
            datacenter_id=datacenter_id
        )
        
        self.generators[generator_id] = generator
        self._save_generator_to_db(generator)
        
        logger(f"[ID] 添加生成器: {name}")
        
        return generator_id
    
    def _save_generator_to_db(self, generator: IDGenerator):
        """保存生成器到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO id_generators 
                (generator_id, name, generator_type, worker_id, datacenter_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                generator.generator_id, generator.name,
                generator.generator_type, generator.worker_id,
                generator.datacenter_id
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[ID] 保存生成器失败: {e}")
    
    def generate_id(self, generator_id: str = 'snowflake_default') -> str:
        """生成ID"""
        generator = self.generators.get(generator_id)
        
        if not generator:
            generator = self.generators.get('snowflake_default')
        
        if not generator:
            import uuid
            return str(uuid.uuid4())
        
        generated_id = generator.generate()
        
        self._log_id_generation(generator_id, generated_id)
        
        return generated_id
    
    def generate_ids(self, generator_id: str = 'snowflake_default',
                     count: int = 10) -> list:
        """批量生成ID"""
        return [self.generate_id(generator_id) for _ in range(count)]
    
    def _log_id_generation(self, generator_id: str, generated_id: str):
        """记录ID生成日志"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO id_generation_logs (generator_id, generated_id)
                VALUES (?, ?)
            ''', (generator_id, generated_id))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[ID] 记录日志失败: {e}")
    
    def next_sequence(self, counter_name: str, step: int = 1) -> int:
        """获取下一个序列值"""
        with self.lock:
            if counter_name not in self.id_counters:
                self.id_counters[counter_name] = 0
            
            value = self.id_counters[counter_name]
            self.id_counters[counter_name] += step
        
        self._update_counter_in_db(counter_name, self.id_counters[counter_name])
        
        return value
    
    def _update_counter_in_db(self, counter_name: str, value: int):
        """更新数据库中的计数器"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO id_counters (counter_name, current_value)
                VALUES (?, ?)
            ''', (counter_name, value))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[ID] 更新计数器失败: {e}")
    
    def set_counter(self, counter_name: str, value: int):
        """设置计数器值"""
        with self.lock:
            self.id_counters[counter_name] = value
        
        self._update_counter_in_db(counter_name, value)
        logger(f"[ID] 设置计数器: {counter_name} = {value}")
    
    def get_counter(self, counter_name: str) -> int:
        """获取计数器值"""
        return self.id_counters.get(counter_name, 0)
    
    def get_generator(self, generator_id: str) -> Optional[IDGenerator]:
        """获取生成器"""
        return self.generators.get(generator_id)
    
    def get_generators(self) -> list:
        """获取所有生成器"""
        return [g.to_dict() for g in self.generators.values()]
    
    def get_id_history(self, generator_id: str = None, limit: int = 100) -> list:
        """获取ID生成历史"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            query = 'SELECT * FROM id_generation_logs WHERE 1=1'
            params = []
            
            if generator_id:
                query += ' AND generator_id = ?'
                params.append(generator_id)
            
            query += ' ORDER BY generated_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            
            columns = [desc[0] for desc in cursor.description]
            history = []
            
            for row in cursor.fetchall():
                history.append(dict(zip(columns, row)))
            
            conn.close()
            return history
        except Exception as e:
            logger(f"[ID] 获取历史失败: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'status': 'running' if self.is_running else 'stopped',
            'total_generators': len(self.generators),
            'total_counters': len(self.id_counters),
            'generators': {k: v.generator_type for k, v in self.generators.items()}
        }
    
    def start(self):
        """启动ID生成服务"""
        if self.is_running:
            return
        
        self.is_running = True
        logger(f"[ID] 分布式ID生成服务已启动")
    
    def stop(self):
        """停止ID生成服务"""
        self.is_running = False
        logger(f"[ID] 分布式ID生成服务已停止")

distributed_id_service = DistributedIDService()
