# -*- coding: utf-8 -*-
#!/usr/bin/env python3
r"""
AI自学习中间件 - 用于收集系统运行数据并发送到AI自学习系统
r"""

import time
import logging
import psutil
from flask import request, g
from app.utils.logging import logger
from app.ai.self_learning_system import self_learning_system
import sys

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format=r'%(asctime)s - AI Self Learning Middleware - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(r'logs/ai_self_learning_middleware.log'),
        logging.StreamHandler()
    ])

class AISelfLearningMiddleware:
    r"""AI自学习中间件类r"""

    def __init__(self):
        self.enabled = True
        logger.info(r"AI自学习中间件初始化完成")

    def ai_self_learning_middleware(self, app):
        r"""AI自学习中间件r"""

        @app.before_request
        def before_request():
            r"""请求前处理: 记录请求开始时间和资源使用情况r"""
            if not self.enabled:
                return

            g.request_start_time = time.time()
            g.request_start_resource = {
                r'cpu_usage': psutil.cpu_percent(),
                r'memory_usage': psutil.virtual_memory().percent,
                r'disk_usage': psutil.disk_usage(r'/').percent,
                r'network_io': psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
            }

            self._record_user_behavior()

        @app.after_request
        def after_request(response):
            r"""请求后处理: 记录响应时间和资源使用情况r"""
            if not self.enabled:
                return response

            try:
                response_time = time.time() - g.request_start_time

                end_resource = {
                    r'cpu_usage': psutil.cpu_percent(),
                    r'memory_usage': psutil.virtual_memory().percent,
                    r'network_io': psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
                }

                resource_diff = {
                    r'cpu_usage': end_resource[r'cpu_usage'],
                    r'memory_usage': end_resource[r'memory_usage'],
                    r'network_io_diff': end_resource[r'network_io'] - g.request_start_resource[r'network_io']
                }

                self._record_performance_data(response_time)
                self._record_resource_usage(resource_diff)

                response.headers[r'X-Response-Time'] = str(response_time)
            except Exception as e:
                logger.error(fr"记录请求数据失败: {str(e)}")

            return response

        def handle_error(error):
            r"""错误处理: 记录错误日志r"""
            if not self.enabled:
                raise error

            try:
                self._record_error_log(error)
            except Exception as e:
                logger.error(fr"记录错误日志失败: {str(e)}")

            raise error

        logger.info(r"AI自学习中间件注册完成")
        return app

    def _record_user_behavior(self):
        r"""记录用户行为r"""
        user_behavior = {
            r'method': request.method,
            r'remote_addr': request.remote_addr,
            r'user_agent': request.headers.get(r'User-Agent', r''),
            r'referer': request.headers.get(r'Referer', r'')
        }

        if hasattr(request, r'user_id'):
            user_behavior[r'user_id'] = request.user_id
        elif r'Authorization' in request.headers:
            pass

        self_learning_system.add_user_behavior(user_behavior)

    def _record_performance_data(self, response_time):
        r"""记录性能数据r"""
        performance_data = {
            r'path': request.path,
            r'method': request.method,
            r'response_time': response_time,
            r'status_code': getattr(g, r'status_code', 200),
            r'remote_addr': request.remote_addr
        }

        self_learning_system.add_performance_data(performance_data)

    def _record_resource_usage(self, resource_diff):
        r"""记录资源使用数据r"""
        resource_data = {
            r'cpu_usage': resource_diff[r'cpu_usage'],
            r'memory_usage': resource_diff[r'memory_usage'],
            r'network_io_diff': resource_diff[r'network_io_diff'],
            r'method': request.method
        }

        self_learning_system.add_resource_usage(resource_data)

    def _record_error_log(self, error):
        r"""记录错误日志r"""
        error_data = {
            r'error_type': type(error).__name__,
            r'message': str(error),
            r'path': request.path,
            r'method': request.method,
            r'remote_addr': request.remote_addr,
            r'user_agent': request.headers.get(r'User-Agent', r'')
        }

        self_learning_system.add_error_log(error_data)

    def set_enabled(self, enabled):
        r"""设置中间件是否启用r"""
        self.enabled = enabled
        logger.info(fr"AI自学习中间件启用状态: {enabled}")
        return enabled
