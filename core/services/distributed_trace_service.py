#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS分布式追踪服务
提供请求链路追踪和性能监控
"""

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = print

class Span:
    """追踪跨度"""
    
    def __init__(self, trace_id: str, span_id: str, parent_span_id: str = None,
                 name: str = '', operation_name: str = '',
                 start_time: float = None, end_time: float = None,
                 tags: Dict[str, Any] = None, logs: List[Dict[str, Any]] = None,
                 status_code: str = 'ok', status_message: str = '',
                 service_name: str = '', resource_name: str = ''):
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_span_id = parent_span_id
        self.name = name
        self.operation_name = operation_name
        self.start_time = start_time or time.time()
        self.end_time = end_time
        self.tags = tags or {}
        self.logs = logs or []
        self.status_code = status_code
        self.status_message = status_message
        self.service_name = service_name
        self.resource_name = resource_name
    
    def finish(self, status_code: str = 'ok', status_message: str = ''):
        """结束跨度"""
        self.end_time = time.time()
        self.status_code = status_code
        self.status_message = status_message
    
    def add_tag(self, key: str, value: Any):
        """添加标签"""
        self.tags[key] = value
    
    def add_log(self, message: str, **kwargs):
        """添加日志"""
        self.logs.append({
            'timestamp': time.time(),
            'message': message,
            **kwargs
        })
    
    def get_duration(self) -> float:
        """获取持续时间"""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'trace_id': self.trace_id,
            'span_id': self.span_id,
            'parent_span_id': self.parent_span_id,
            'name': self.name,
            'operation_name': self.operation_name,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.get_duration(),
            'tags': self.tags,
            'logs': self.logs,
            'status_code': self.status_code,
            'status_message': self.status_message,
            'service_name': self.service_name,
            'resource_name': self.resource_name
        }

class Trace:
    """追踪"""
    
    def __init__(self, trace_id: str, name: str = '',
                 start_time: float = None, end_time: float = None):
        self.trace_id = trace_id
        self.name = name
        self.start_time = start_time or time.time()
        self.end_time = end_time
        self.spans: Dict[str, Span] = {}
    
    def add_span(self, span: Span):
        """添加跨度"""
        self.spans[span.span_id] = span
    
    def finish(self):
        """结束追踪"""
        self.end_time = time.time()
    
    def get_duration(self) -> float:
        """获取持续时间"""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'trace_id': self.trace_id,
            'name': self.name,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.get_duration(),
            'span_count': len(self.spans),
            'spans': [span.to_dict() for span in self.spans.values()]
        }

class DistributedTraceService:
    """分布式追踪服务"""
    
    def __init__(self):
        self.traces: Dict[str, Trace] = {}
        self.active_traces: Dict[str, Trace] = {}
        self.is_running = False
        self.lock = threading.Lock()
        
        self.config = self._load_config()
        self._init_database()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'trace_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'max_active_traces': 1000,
            'max_trace_duration': 3600,
            'sampling_rate': 1.0,
            'auto_cleanup_enabled': True,
            'cleanup_interval': 60
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'trace_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS traces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trace_id TEXT NOT NULL UNIQUE,
                    name TEXT,
                    start_time REAL,
                    end_time REAL,
                    duration REAL,
                    span_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS spans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    span_id TEXT NOT NULL UNIQUE,
                    trace_id TEXT NOT NULL,
                    parent_span_id TEXT,
                    name TEXT,
                    operation_name TEXT,
                    start_time REAL,
                    end_time REAL,
                    duration REAL,
                    status_code TEXT DEFAULT 'ok',
                    status_message TEXT,
                    service_name TEXT,
                    resource_name TEXT,
                    tags TEXT,
                    logs TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trace_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_name TEXT NOT NULL,
                    operation_name TEXT NOT NULL,
                    count INTEGER DEFAULT 0,
                    total_duration REAL DEFAULT 0.0,
                    avg_duration REAL DEFAULT 0.0,
                    min_duration REAL DEFAULT 0.0,
                    max_duration REAL DEFAULT 0.0,
                    error_count INTEGER DEFAULT 0,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_traces_id ON traces(trace_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_spans_trace ON spans(trace_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_spans_span ON spans(span_id)
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[追踪] 初始化数据库失败: {e}")
    
    def _generate_trace_id(self) -> str:
        """生成追踪ID"""
        import uuid
        return str(uuid.uuid4())
    
    def _generate_span_id(self) -> str:
        """生成跨度ID"""
        import uuid
        return str(uuid.uuid4())[:16]
    
    def start_trace(self, name: str = '') -> str:
        """开始追踪"""
        if not self.config['enabled']:
            import uuid
            return str(uuid.uuid4())
        
        trace_id = self._generate_trace_id()
        
        trace = Trace(trace_id=trace_id, name=name)
        
        with self.lock:
            self.active_traces[trace_id] = trace
            if len(self.active_traces) > self.config['max_active_traces']:
                oldest = min(self.active_traces.keys(), key=lambda k: self.active_traces[k].start_time)
                self._save_trace(self.active_traces[oldest])
                del self.active_traces[oldest]
        
        logger(f"[追踪] 开始追踪: {trace_id} - {name}")
        
        return trace_id
    
    def start_span(self, trace_id: str, name: str = '', operation_name: str = '',
                   parent_span_id: str = None, service_name: str = '',
                   resource_name: str = '') -> str:
        """开始跨度"""
        if not self.config['enabled']:
            return self._generate_span_id()
        
        span_id = self._generate_span_id()
        
        with self.lock:
            trace = self.active_traces.get(trace_id)
            
            if trace:
                span = Span(
                    trace_id=trace_id,
                    span_id=span_id,
                    parent_span_id=parent_span_id,
                    name=name,
                    operation_name=operation_name,
                    service_name=service_name,
                    resource_name=resource_name
                )
                
                trace.add_span(span)
                
                return span_id
        
        return span_id
    
    def finish_span(self, trace_id: str, span_id: str,
                    status_code: str = 'ok', status_message: str = ''):
        """结束跨度"""
        if not self.config['enabled']:
            return
        
        with self.lock:
            trace = self.active_traces.get(trace_id)
            
            if trace and span_id in trace.spans:
                trace.spans[span_id].finish(status_code, status_message)
                
                self._update_stats(trace.spans[span_id])
    
    def finish_trace(self, trace_id: str):
        """结束追踪"""
        if not self.config['enabled']:
            return
        
        with self.lock:
            trace = self.active_traces.get(trace_id)
            
            if trace:
                trace.finish()
                
                self._save_trace(trace)
                
                del self.active_traces[trace_id]
        
        logger(f"[追踪] 结束追踪: {trace_id}")
    
    def _save_trace(self, trace: Trace):
        """保存追踪到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO traces 
                (trace_id, name, start_time, end_time, duration, span_count, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                trace.trace_id, trace.name,
                trace.start_time, trace.end_time,
                trace.get_duration(), len(trace.spans),
                'completed' if trace.end_time else 'active'
            ))
            
            for span in trace.spans.values():
                cursor.execute('''
                    INSERT OR REPLACE INTO spans 
                    (span_id, trace_id, parent_span_id, name, operation_name,
                     start_time, end_time, duration, status_code, status_message,
                     service_name, resource_name, tags, logs)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    span.span_id, span.trace_id, span.parent_span_id,
                    span.name, span.operation_name,
                    span.start_time, span.end_time,
                    span.get_duration(), span.status_code,
                    span.status_message, span.service_name,
                    span.resource_name, json.dumps(span.tags),
                    json.dumps(span.logs)
                ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[追踪] 保存追踪失败: {e}")
    
    def _update_stats(self, span: Span):
        """更新统计"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT count, total_duration, min_duration, max_duration, error_count 
                FROM trace_stats 
                WHERE service_name = ? AND operation_name = ?
            ''', (span.service_name or 'unknown', span.operation_name or 'unknown'))
            
            row = cursor.fetchone()
            
            if row:
                count = row[0] + 1
                total_duration = row[1] + span.get_duration()
                min_duration = min(row[2], span.get_duration()) if row[2] else span.get_duration()
                max_duration = max(row[3], span.get_duration()) if row[3] else span.get_duration()
                error_count = row[4] + (1 if span.status_code != 'ok' else 0)
                avg_duration = total_duration / count
                
                cursor.execute('''
                    UPDATE trace_stats 
                    SET count = ?, total_duration = ?, avg_duration = ?, 
                        min_duration = ?, max_duration = ?, error_count = ?, timestamp = ?
                    WHERE service_name = ? AND operation_name = ?
                ''', (count, total_duration, avg_duration, min_duration,
                      max_duration, error_count, datetime.now().isoformat(),
                      span.service_name or 'unknown', span.operation_name or 'unknown'))
            else:
                cursor.execute('''
                    INSERT INTO trace_stats 
                    (service_name, operation_name, count, total_duration, avg_duration,
                     min_duration, max_duration, error_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    span.service_name or 'unknown', span.operation_name or 'unknown',
                    1, span.get_duration(), span.get_duration(),
                    span.get_duration(), span.get_duration(),
                    1 if span.status_code != 'ok' else 0
                ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[追踪] 更新统计失败: {e}")
    
    def annotate_span(self, trace_id: str, span_id: str, **kwargs):
        """标注跨度"""
        if not self.config['enabled']:
            return
        
        with self.lock:
            trace = self.active_traces.get(trace_id)
            
            if trace and span_id in trace.spans:
                span = trace.spans[span_id]
                
                for key, value in kwargs.items():
                    span.add_tag(key, value)
    
    def log_span(self, trace_id: str, span_id: str, message: str, **kwargs):
        """记录跨度日志"""
        if not self.config['enabled']:
            return
        
        with self.lock:
            trace = self.active_traces.get(trace_id)
            
            if trace and span_id in trace.spans:
                trace.spans[span_id].add_log(message, **kwargs)
    
    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """获取追踪"""
        with self.lock:
            if trace_id in self.active_traces:
                return self.active_traces[trace_id]
        
        return self._load_trace_from_db(trace_id)
    
    def _load_trace_from_db(self, trace_id: str) -> Optional[Trace]:
        """从数据库加载追踪"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM traces WHERE trace_id = ?', (trace_id,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return None
            
            columns = [desc[0] for desc in cursor.description]
            trace_data = dict(zip(columns, row))
            
            trace = Trace(
                trace_id=trace_data['trace_id'],
                name=trace_data['name'],
                start_time=trace_data['start_time'],
                end_time=trace_data['end_time']
            )
            
            cursor.execute('SELECT * FROM spans WHERE trace_id = ?', (trace_id,))
            
            for span_row in cursor.fetchall():
                span_columns = [desc[0] for desc in cursor.description]
                span_data = dict(zip(span_columns, span_row))
                
                span = Span(
                    trace_id=span_data['trace_id'],
                    span_id=span_data['span_id'],
                    parent_span_id=span_data['parent_span_id'],
                    name=span_data['name'],
                    operation_name=span_data['operation_name'],
                    start_time=span_data['start_time'],
                    end_time=span_data['end_time'],
                    status_code=span_data['status_code'],
                    status_message=span_data['status_message'],
                    service_name=span_data['service_name'],
                    resource_name=span_data['resource_name'],
                    tags=json.loads(span_data['tags'] or '{}'),
                    logs=json.loads(span_data['logs'] or '[]')
                )
                
                trace.add_span(span)
            
            conn.close()
            return trace
        except Exception as e:
            logger(f"[追踪] 加载追踪失败: {e}")
            return None
    
    def get_traces(self, limit: int = 100, status: str = None) -> List[Trace]:
        """获取追踪列表"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            query = 'SELECT trace_id FROM traces WHERE 1=1'
            params = []
            
            if status:
                query += ' AND status = ?'
                params.append(status)
            
            query += ' ORDER BY start_time DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            
            traces = []
            
            for row in cursor.fetchall():
                trace = self.get_trace(row[0])
                if trace:
                    traces.append(trace)
            
            conn.close()
            return traces
        except Exception as e:
            logger(f"[追踪] 获取追踪列表失败: {e}")
            return []
    
    def get_trace_stats(self, service_name: str = None, operation_name: str = None) -> List[Dict[str, Any]]:
        """获取追踪统计"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            query = 'SELECT * FROM trace_stats WHERE 1=1'
            params = []
            
            if service_name:
                query += ' AND service_name = ?'
                params.append(service_name)
            if operation_name:
                query += ' AND operation_name = ?'
                params.append(operation_name)
            
            query += ' ORDER BY count DESC'
            
            cursor.execute(query, params)
            
            columns = [desc[0] for desc in cursor.description]
            stats = []
            
            for row in cursor.fetchall():
                stats.append(dict(zip(columns, row)))
            
            conn.close()
            return stats
        except Exception as e:
            logger(f"[追踪] 获取统计失败: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        with self.lock:
            return {
                'status': 'running' if self.is_running else 'stopped',
                'enabled': self.config['enabled'],
                'active_traces': len(self.active_traces),
                'max_active_traces': self.config['max_active_traces'],
                'sampling_rate': self.config['sampling_rate'],
                'auto_cleanup_enabled': self.config['auto_cleanup_enabled']
            }
    
    def start(self):
        """启动追踪服务"""
        if self.is_running:
            return
        
        self.is_running = True
        self._start_cleanup_thread()
        logger(f"[追踪] 分布式追踪服务已启动")
    
    def _start_cleanup_thread(self):
        """启动清理线程"""
        def cleanup():
            while self.is_running:
                time.sleep(self.config['cleanup_interval'])
                
                with self.lock:
                    now = time.time()
                    expired = []
                    
                    for trace_id, trace in self.active_traces.items():
                        if now - trace.start_time > self.config['max_trace_duration']:
                            expired.append(trace_id)
                    
                    for trace_id in expired:
                        trace = self.active_traces[trace_id]
                        trace.finish()
                        self._save_trace(trace)
                        del self.active_traces[trace_id]
        
        thread = threading.Thread(target=cleanup, daemon=True)
        thread.start()
    
    def stop(self):
        """停止追踪服务"""
        self.is_running = False
        
        with self.lock:
            for trace in self.active_traces.values():
                trace.finish()
                self._save_trace(trace)
            
            self.active_traces.clear()
        
        logger(f"[追踪] 分布式追踪服务已停止")

distributed_trace_service = DistributedTraceService()
