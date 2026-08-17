#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS日志聚合服务
提供统一的结构化日志收集、查询和分析
"""

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from collections import defaultdict, deque

logger = print

# 日志级别
LOG_LEVELS = {'DEBUG': 10, 'INFO': 20, 'WARNING': 30, 'ERROR': 40, 'CRITICAL': 50}


class LogEntry:
    """日志条目"""

    def __init__(self, log_id: str, level: str, source: str, message: str,
                 timestamp: str = None, trace_id: str = '',
                 user_id: str = '', extra: Dict[str, Any] = None):
        self.log_id = log_id
        self.level = level.upper()
        self.source = source
        self.message = message
        self.timestamp = timestamp or datetime.now().isoformat()
        self.trace_id = trace_id
        self.user_id = user_id
        self.extra = extra or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            'log_id': self.log_id,
            'level': self.level,
            'source': self.source,
            'message': self.message,
            'timestamp': self.timestamp,
            'trace_id': self.trace_id,
            'user_id': self.user_id,
            'extra': self.extra
        }


class LogAggregationService:
    """日志聚合服务"""

    def __init__(self, buffer_size: int = 10000, flush_interval: int = 5):
        self.buffer: deque = deque(maxlen=buffer_size)
        self.flush_interval = flush_interval
        self.is_running = False
        self.flush_thread = None
        self.lock = threading.Lock()

        self._pending_writes: List[LogEntry] = []
        self._write_lock = threading.Lock()

        self.min_level = 'INFO'
        self.sources_filter: Optional[List[str]] = None

        self._init_database()

    def _init_database(self):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS aggregated_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    log_id TEXT NOT NULL,
                    level TEXT NOT NULL,
                    source TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    trace_id TEXT,
                    user_id TEXT,
                    extra TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS log_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_name TEXT NOT NULL UNIQUE,
                    log_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    last_log_at TEXT,
                    registered_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_logs_level ON aggregated_logs(level)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_logs_source ON aggregated_logs(source)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON aggregated_logs(timestamp)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_logs_trace ON aggregated_logs(trace_id)
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[日志聚合] 初始化数据库失败: {e}")

    def log(self, level: str, source: str, message: str,
            trace_id: str = '', user_id: str = '',
            extra: Dict[str, Any] = None) -> str:
        """记录日志"""
        level = level.upper()

        if LOG_LEVELS.get(level, 0) < LOG_LEVELS.get(self.min_level, 0):
            return ''

        if self.sources_filter and source not in self.sources_filter:
            return ''

        import uuid
        log_id = f"log_{uuid.uuid4().hex[:16]}"

        entry = LogEntry(
            log_id=log_id,
            level=level,
            source=source,
            message=message,
            trace_id=trace_id,
            user_id=user_id,
            extra=extra or {}
        )

        with self.lock:
            self.buffer.append(entry)
            self._pending_writes.append(entry)

        return log_id

    def debug(self, source: str, message: str, **kwargs):
        return self.log('DEBUG', source, message, **kwargs)

    def info(self, source: str, message: str, **kwargs):
        return self.log('INFO', source, message, **kwargs)

    def warning(self, source: str, message: str, **kwargs):
        return self.log('WARNING', source, message, **kwargs)

    def error(self, source: str, message: str, **kwargs):
        return self.log('ERROR', source, message, **kwargs)

    def critical(self, source: str, message: str, **kwargs):
        return self.log('CRITICAL', source, message, **kwargs)

    def _flush_loop(self):
        """定期写入数据库"""
        while self.is_running:
            time.sleep(self.flush_interval)
            self._flush()

    def _flush(self):
        """将待写日志批量写入数据库"""
        with self._write_lock:
            if not self._pending_writes:
                return

            entries = self._pending_writes[:]
            self._pending_writes.clear()

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            source_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {'total': 0, 'errors': 0, 'last': ''})

            for entry in entries:
                cursor.execute('''
                    INSERT INTO aggregated_logs
                    (log_id, level, source, message, timestamp, trace_id, user_id, extra)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    entry.log_id, entry.level, entry.source,
                    entry.message, entry.timestamp,
                    entry.trace_id, entry.user_id,
                    json.dumps(entry.extra)
                ))

                stats = source_stats[entry.source]
                stats['total'] += 1
                stats['last'] = entry.timestamp
                if entry.level in ('ERROR', 'CRITICAL'):
                    stats['errors'] += 1

            for source, stats in source_stats.items():
                cursor.execute('''
                    INSERT OR IGNORE INTO log_sources (source_name) VALUES (?)
                ''', (source,))

                cursor.execute('''
                    UPDATE log_sources
                    SET log_count = log_count + ?,
                        error_count = error_count + ?,
                        last_log_at = ?
                    WHERE source_name = ?
                ''', (stats['total'], stats['errors'], stats['last'], source))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[日志聚合] 批量写入失败: {e}")

    def query(self, level: str = None, source: str = None,
              trace_id: str = None, user_id: str = None,
              keyword: str = None, start_time: str = None,
              end_time: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """查询日志"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            query = 'SELECT * FROM aggregated_logs WHERE 1=1'
            params = []

            if level:
                query += ' AND level = ?'
                params.append(level.upper())
            if source:
                query += ' AND source = ?'
                params.append(source)
            if trace_id:
                query += ' AND trace_id = ?'
                params.append(trace_id)
            if user_id:
                query += ' AND user_id = ?'
                params.append(user_id)
            if keyword:
                query += ' AND message LIKE ?'
                params.append(f"%{keyword}%")
            if start_time:
                query += ' AND timestamp >= ?'
                params.append(start_time)
            if end_time:
                query += ' AND timestamp <= ?'
                params.append(end_time)

            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)

            columns = [desc[0] for desc in cursor.description]
            logs = [dict(zip(columns, row)) for row in cursor.fetchall()]

            conn.close()
            return logs
        except Exception as e:
            logger(f"[日志聚合] 查询失败: {e}")
            return []

    def get_recent(self, count: int = 50) -> List[Dict[str, Any]]:
        """获取最近日志（从内存缓冲区）"""
        with self.lock:
            entries = list(self.buffer)[-count:]
        return [e.to_dict() for e in entries]

    def get_sources(self) -> List[Dict[str, Any]]:
        """获取所有日志源"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM log_sources ORDER BY last_log_at DESC
            ''')

            columns = [desc[0] for desc in cursor.description]
            sources = [dict(zip(columns, row)) for row in cursor.fetchall()]

            conn.close()
            return sources
        except Exception as e:
            logger(f"[日志聚合] 获取日志源失败: {e}")
            return []

    def get_stats(self, hours: int = 24) -> Dict[str, Any]:
        """获取日志统计"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            since = (datetime.now() - timedelta(hours=hours)).isoformat()

            cursor.execute('''
                SELECT level, COUNT(*) as count
                FROM aggregated_logs
                WHERE timestamp >= ?
                GROUP BY level
            ''', (since,))

            level_stats = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute('''
                SELECT source, COUNT(*) as count
                FROM aggregated_logs
                WHERE timestamp >= ?
                GROUP BY source
                ORDER BY count DESC
                LIMIT 10
            ''', (since,))

            top_sources = {row[0]: row[1] for row in cursor.fetchall()}

            conn.close()

            return {
                'hours': hours,
                'total': sum(level_stats.values()),
                'by_level': level_stats,
                'top_sources': top_sources,
                'buffer_size': len(self.buffer)
            }
        except Exception as e:
            logger(f"[日志聚合] 获取统计失败: {e}")
            return {}

    def set_min_level(self, level: str):
        """设置最低日志级别"""
        self.min_level = level.upper()

    def cleanup_old_logs(self, days: int = 30):
        """清理旧日志"""
        try:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()

            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('DELETE FROM aggregated_logs WHERE timestamp < ?', (cutoff,))

            deleted = cursor.rowcount
            conn.commit()
            conn.close()

            logger(f"[日志聚合] 清理 {days} 天前日志: {deleted} 条")
            return deleted
        except Exception as e:
            logger(f"[日志聚合] 清理失败: {e}")
            return 0

    def get_status(self) -> Dict[str, Any]:
        return {
            'status': 'running' if self.is_running else 'stopped',
            'buffer_size': len(self.buffer),
            'pending_writes': len(self._pending_writes),
            'min_level': self.min_level,
            'flush_interval': self.flush_interval
        }

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self.flush_thread.start()
        logger(f"[日志聚合] 日志聚合服务已启动")

    def stop(self):
        self.is_running = False
        if self.flush_thread:
            self.flush_thread.join(timeout=10)
        self._flush()
        logger(f"[日志聚合] 日志聚合服务已停止")


log_aggregation_service = LogAggregationService()
