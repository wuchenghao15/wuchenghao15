# -*- coding: utf-8 -*-
#!/usr/bin/env python3
r"""
AI中间件学习系统
用于监控和分析中间件性能 - 实现AI驱动的中间件优化
r"""

import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
import threading
import sqlite3

from app.utils.logging import logger
from flask import request

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format=r'%(asctime)s - AI Middleware Learning - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(r'logs/ai_middleware_learning.log'),
        logging.StreamHandler()
    ])

class AIMiddlewareLearningSystem:
    r"""AI中间件学习系统r"""

    def __init__(self):
        self.performance_data = []
        self.lock = threading.Lock()
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), r'../../dev.db')
        self.ai_brain_integration = None

        self._init_database()

        logger.info(r"AI中间件学习系统初始化完成")

    def _init_database(self):
        r"""初始化数据库表r"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(r'''
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
            r''')

            cursor.execute(r'''
            CREATE TABLE IF NOT EXISTS middleware_optimization_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                middleware_name TEXT NOT NULL,
                suggestion TEXT NOT NULL,
                confidence REAL NOT NULL,
                created_at DATETIME NOT NULL,
                applied INTEGER DEFAULT 0,
                effectiveness REAL DEFAULT NULL
            )
            r''')

            conn.commit()

    def monitor_middleware_performance(self, middleware_name: str, app):
        r"""监控中间件性能r"""
        @app.before_request
        def before_middleware():
            if hasattr(request, r'middleware_start_times'):
                request.middleware_start_times[middleware_name] = time.time()
            else:
                request.middleware_start_times = {middleware_name: time.time()}

        @app.after_request
        def after_middleware(response):
            if hasattr(request, r'middleware_start_times') and middleware_name in request.middleware_start_times:
                start_time = request.middleware_start_times[middleware_name]
                end_time = time.time()
                duration = end_time - start_time

                performance_data = {
                    r'middleware_name': middleware_name,
                    r'request_path': request.path,
                    r'method': request.method,
                    r'start_time': start_time,
                    r'end_time': end_time,
                    r'duration': duration,
                    r'status_code': response.status_code,
                    r'client_ip': request.remote_addr,
                    r'timestamp': datetime.now().isoformat(),
                    r'cpu_usage': None,
                    r'memory_usage': None
                }

                self.save_performance_data(performance_data)
                self.analyze_performance_data(middleware_name)

            return response

        return app

    def save_performance_data(self, data: Dict):
        r"""保存性能数据到数据库r"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(r'''
            INSERT INTO middleware_performance (
                middleware_name, request_path, method, start_time, end_time,
                duration, status_code, client_ip, timestamp, cpu_usage, memory_usage
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            r''', (
                data[r'middleware_name'],
                data[r'request_path'],
                data[r'method'],
                data[r'start_time'],
                data[r'end_time'],
                data[r'duration'],
                data[r'status_code'],
                data[r'client_ip'],
                data[r'timestamp'],
                data[r'cpu_usage'],
                data[r'memory_usage']
            ))

            conn.commit()

    def analyze_performance_data(self, middleware_name: str):
        r"""分析中间件性能数据r"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(r'''
            SELECT duration, status_code FROM middleware_performance
            WHERE middleware_name = ?
            ORDER BY timestamp DESC
            LIMIT 100
            r''', (middleware_name,))
            data = cursor.fetchall()

        if len(data) < 10:
            return

        durations = [row[0] for row in data]
        status_codes = [row[1] for row in data]

        metrics = {
            r'avg_duration': sum(durations) / len(durations),
            r'p95_duration': sorted(durations)[int(len(durations) * 0.95)] if len(durations) >= 20 else max(durations),
            r'error_rate': sum(1 for s in status_codes if s >= 400) / len(status_codes)
        }

        self.generate_optimization_suggestions(middleware_name, metrics)

    def generate_optimization_suggestions(self, middleware_name: str, metrics: Dict):
        r"""生成优化建议r"""
        suggestions = []

        if metrics[r'p95_duration'] > 0.1:
            suggestions.append({
                r'suggestion': f"中间件 {middleware_name} 95%响应时间较长 ({metrics[r'p95_duration']:.4f}s),建议优化算法或增加缓存",
                r'confidence': 0.8
            })

        if metrics[r'error_rate'] > 0.05:
            suggestions.append({
                r'suggestion': f"中间件 {middleware_name} 错误率较高 ({metrics[r'error_rate']:.4f}),建议检查错误处理逻辑",
                r'confidence': 0.9
            })

        if metrics[r'avg_duration'] > 0.05:
            suggestions.append({
                r'suggestion': f"中间件 {middleware_name} 平均响应时间较长 ({metrics[r'avg_duration']:.4f}s),建议优化代码或增加异步处理",
                r'confidence': 0.7
            })

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for suggestion in suggestions:
                cursor.execute(r'''
                INSERT INTO middleware_optimization_suggestions (
                    middleware_name, suggestion, confidence, created_at
                ) VALUES (?, ?, ?, ?)
                r''', (
                    middleware_name,
                    suggestion[r'suggestion'],
                    suggestion[r'confidence'],
                    datetime.now().isoformat()
                ))

            conn.commit()

        if suggestions:
            logger.info(fr"为中间件 {middleware_name} 生成了 {len(suggestions)} 条优化建议")

    def get_optimization_suggestions(self, middleware_name: Optional[str] = None) -> List[Dict]:
        r"""获取优化建议r"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if middleware_name:
            cursor.execute(r'''
            SELECT id, middleware_name, suggestion, confidence, created_at, applied, effectiveness
            FROM middleware_optimization_suggestions
            WHERE middleware_name = ?
            ORDER BY confidence DESC
            r''', (middleware_name,))
        else:
            cursor.execute(r'''
            SELECT id, middleware_name, suggestion, confidence, created_at, applied, effectiveness
            FROM middleware_optimization_suggestions
            ORDER BY confidence DESC
            r''')

        rows = cursor.fetchall()
        conn.close()

        suggestions = []
        for row in rows:
            suggestions.append({
                r'id': row[0],
                r'middleware_name': row[1],
                r'suggestion': row[2],
                r'confidence': row[3],
                r'created_at': row[4],
                r'applied': bool(row[5]),
                r'effectiveness': row[6]
            })

        return suggestions


def ai_middleware_learning_middleware(app):
    r"""AI中间件学习中间件r"""

    @app.before_request
    def before_request_middleware():
        request.middleware_start_times = {}
        request.start_time = time.time()

    @app.after_request
    def after_request_middleware(response):
        if hasattr(request, r'start_time'):
            total_duration = time.time() - request.start_time
            logging.info(fr"请求完成: {request.method} {request.path} {response.status_code} {total_duration:.4f}s")
        return response

    return app
