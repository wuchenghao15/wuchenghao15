# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI自学习中间件 - 用于收集系统运行数据并发送到AI自学习系统
"""

import time
import logging
import psutil
from flask import request, g
from app.utils.logging import logger
from app.ai.self_learning_system import self_learning_system
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - AI Self Learning Middleware - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ai_self_learning_middleware.log'),
        logging.StreamHandler()
    ])

class AISelfLearningMiddleware:
    """AI自学习中间件类"""

    def __init__(self):
        self.enabled = True
        logger.info("AI自学习中间件初始化完成")

    def ai_self_learning_middleware(self, app):
        """AI自学习中间件"""

        @app.before_request
        def before_request():
            """请求前处理: 记录请求开始时间和资源使用情况"""
            if not self.enabled:
                return

            g.request_start_time = time.time()
            g.request_start_resource = {
                'cpu_usage': psutil.cpu_percent(),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'network_io': psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
            }

            self._record_user_behavior()

        @app.after_request
        def after_request(response):
            """请求后处理: 记录响应时间和资源使用情况"""
            if not self.enabled:
                return response

            try:
                response_time = time.time() - g.request_start_time

                end_resource = {
                    'cpu_usage': psutil.cpu_percent(),
                    'memory_usage': psutil.virtual_memory().percent,
                    'network_io': psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
                }

                resource_diff = {
                    'cpu_usage': end_resource['cpu_usage'],
                    'memory_usage': end_resource['memory_usage'],
                    'network_io_diff': end_resource['network_io'] - g.request_start_resource['network_io']
                }

                self._record_performance_data(response_time)
                self._record_resource_usage(resource_diff)

                response.headers['X-Response-Time'] = str(response_time)
            except Exception as e:
                logger.error(f"记录请求数据失败: {str(e)}")

            return response

        def handle_error(error):
            """错误处理: 记录错误日志"""
            if not self.enabled:
                raise error

            try:
                self._record_error_log(error)
            except Exception as e:
                logger.error(f"记录错误日志失败: {str(e)}")

            raise error

        logger.info("AI自学习中间件注册完成")
        return app

    def _record_user_behavior(self):
        """记录用户行为"""
        user_behavior = {
            'method': request.method,
            'remote_addr': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'referer': request.headers.get('Referer', '')
        }

        if hasattr(request, 'user_id'):
            user_behavior['user_id'] = request.user_id
        elif 'Authorization' in request.headers:
            pass

        self_learning_system.add_user_behavior(user_behavior)

    def _record_performance_data(self, response_time):
        """记录性能数据"""
        performance_data = {
            'path': request.path,
            'method': request.method,
            'response_time': response_time,
            'status_code': getattr(g, 'status_code', 200),
            'remote_addr': request.remote_addr
        }

        self_learning_system.add_performance_data(performance_data)

    def _record_resource_usage(self, resource_diff):
        """记录资源使用数据"""
        resource_data = {
            'cpu_usage': resource_diff['cpu_usage'],
            'memory_usage': resource_diff['memory_usage'],
            'network_io_diff': resource_diff['network_io_diff'],
            'method': request.method
        }

        self_learning_system.add_resource_usage(resource_data)

    def _record_error_log(self, error):
        """记录错误日志"""
        error_data = {
            'error_type': type(error).__name__,
            'message': str(error),
            'path': request.path,
            'method': request.method,
            'remote_addr': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')
        }

        self_learning_system.add_error_log(error_data)

    def set_enabled(self, enabled):
        """设置中间件是否启用"""
        self.enabled = enabled
        logger.info(f"AI自学习中间件启用状态: {enabled}")
        return enabled
