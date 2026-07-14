# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI中间件学习系统
用于监控和分析中间件性能 - 实现AI驱动的中间件优化
"""

import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
import threading
import sqlite3

from app.utils.logging import logger
from flask import request

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - AI Middleware Learning - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ai_middleware_learning.log'),
        logging.StreamHandler()
    ])

class AIMiddlewareLearningSystem:
    """AI中间件学习系统"""

    def __init__(self):
        self.performance_data = []
        self.lock = threading.Lock()
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../dev.db')
        self.ai_brain_integration = None

        self._init_database()

        logger.info("AI中间件学习系统初始化完成")

    def _init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS middleware_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                middleware_name TEXT NOT NULL,
                request_path TEXT NOT NULL,
                method TEXT NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL NOT NULL,
                duration REAL NOT NULL,
                status_code INTEGER NOT NULL,
                client_ip TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                cpu_usage REAL,
                memory_usage REAL
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS middleware_optimization_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                middleware_name TEXT NOT NULL,
                suggestion TEXT NOT NULL,
                confidence REAL NOT NULL,
                created_at DATETIME NOT NULL,
                applied INTEGER DEFAULT 0,
                effectiveness REAL DEFAULT NULL
            )
            ''')

            conn.commit()

    def monitor_middleware_performance(self, middleware_name: str, app):
        """监控中间件性能"""
        @app.before_request
        def before_middleware():
            if hasattr(request, 'middleware_start_times'):
                request.middleware_start_times[middleware_name] = time.time()
            else:
                request.middleware_start_times = {middleware_name: time.time()}

        @app.after_request
        def after_middleware(response):
            if hasattr(request, 'middleware_start_times') and middleware_name in request.middleware_start_times:
                start_time = request.middleware_start_times[middleware_name]
                end_time = time.time()
                duration = end_time - start_time

                performance_data = {
                    'middleware_name': middleware_name,
                    'request_path': request.path,
                    'method': request.method,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': duration,
                    'status_code': response.status_code,
                    'client_ip': request.remote_addr,
                    'timestamp': datetime.now().isoformat(),
                    'cpu_usage': None,
                    'memory_usage': None
                }

                self.save_performance_data(performance_data)
                self.analyze_performance_data(middleware_name)

            return response

        return app

    def save_performance_data(self, data: Dict):
        """保存性能数据到数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
            INSERT INTO middleware_performance (
                middleware_name, request_path, method, start_time, end_time,
                duration, status_code, client_ip, timestamp, cpu_usage, memory_usage
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['middleware_name'],
                data['request_path'],
                data['method'],
                data['start_time'],
                data['end_time'],
                data['duration'],
                data['status_code'],
                data['client_ip'],
                data['timestamp'],
                data['cpu_usage'],
                data['memory_usage']
            ))

            conn.commit()

    def analyze_performance_data(self, middleware_name: str):
        """分析中间件性能数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
            SELECT duration, status_code FROM middleware_performance
            WHERE middleware_name = ?
            ORDER BY timestamp DESC
            LIMIT 100
            ''', (middleware_name,))
            data = cursor.fetchall()

        if len(data) < 10:
            return

        durations = [row[0] for row in data]
        status_codes = [row[1] for row in data]

        metrics = {
            'avg_duration': sum(durations) / len(durations),
            'p95_duration': sorted(durations)[int(len(durations) * 0.95)] if len(durations) >= 20 else max(durations),
            'error_rate': sum(1 for s in status_codes if s >= 400) / len(status_codes)
        }

        self.generate_optimization_suggestions(middleware_name, metrics)

    def generate_optimization_suggestions(self, middleware_name: str, metrics: Dict):
        """生成优化建议"""
        suggestions = []

        if metrics['p95_duration'] > 0.1:
            suggestions.append({
                'suggestion': f"中间件 {middleware_name} 95%响应时间较长 ({metrics['p95_duration']:.4f}s),建议优化算法或增加缓存",
                'confidence': 0.8
            })

        if metrics['error_rate'] > 0.05:
            suggestions.append({
                'suggestion': f"中间件 {middleware_name} 错误率较高 ({metrics['error_rate']:.4f}),建议检查错误处理逻辑",
                'confidence': 0.9
            })

        if metrics['avg_duration'] > 0.05:
            suggestions.append({
                'suggestion': f"中间件 {middleware_name} 平均响应时间较长 ({metrics['avg_duration']:.4f}s),建议优化代码或增加异步处理",
                'confidence': 0.7
            })

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for suggestion in suggestions:
                cursor.execute('''
                INSERT INTO middleware_optimization_suggestions (
                    middleware_name, suggestion, confidence, created_at
                ) VALUES (?, ?, ?, ?)
                ''', (
                    middleware_name,
                    suggestion['suggestion'],
                    suggestion['confidence'],
                    datetime.now().isoformat()
                ))

            conn.commit()

        if suggestions:
            logger.info(f"为中间件 {middleware_name} 生成了 {len(suggestions)} 条优化建议")

    def get_optimization_suggestions(self, middleware_name: Optional[str] = None) -> List[Dict]:
        """获取优化建议"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if middleware_name:
            cursor.execute('''
            SELECT id, middleware_name, suggestion, confidence, created_at, applied, effectiveness
            FROM middleware_optimization_suggestions
            WHERE middleware_name = ?
            ORDER BY confidence DESC
            ''', (middleware_name,))
        else:
            cursor.execute('''
            SELECT id, middleware_name, suggestion, confidence, created_at, applied, effectiveness
            FROM middleware_optimization_suggestions
            ORDER BY confidence DESC
            ''')

        rows = cursor.fetchall()
        conn.close()

        suggestions = []
        for row in rows:
            suggestions.append({
                'id': row[0],
                'middleware_name': row[1],
                'suggestion': row[2],
                'confidence': row[3],
                'created_at': row[4],
                'applied': bool(row[5]),
                'effectiveness': row[6]
            })

        return suggestions


def ai_middleware_learning_middleware(app):
    """AI中间件学习中间件"""

    @app.before_request
    def before_request_middleware():
        request.middleware_start_times = {}
        request.start_time = time.time()

    @app.after_request
    def after_request_middleware(response):
        if hasattr(request, 'start_time'):
            total_duration = time.time() - request.start_time
            logging.info(f"请求完成: {request.method} {request.path} {response.status_code} {total_duration:.4f}s")
        return response

    return app
