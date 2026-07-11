# -*- coding: utf-8 -*-
from flask import request, g
import time
import logging
import json

try:
    from app.utils.logging import logger
except ImportError:
    logger = logging.getLogger(__name__)

try:
    from app.ai.monitoring import ai_monitor
except ImportError:
    class FakeAiMonitor:
        @staticmethod
        def log_error(**kwargs):
            logger.warning(f"[AI监控] {kwargs.get('error_message', '')}")
    ai_monitor = FakeAiMonitor()

try:
    from app.utils.network import network_optimizer
except ImportError:
    class FakeNetworkOptimizer:
        @staticmethod
        def rate_limit_check(ip):
            return False
        @staticmethod
        def is_duplicate_request(ip, endpoint, data):
            return False
        @staticmethod
        def update_performance_metrics(response_time):
            pass
    network_optimizer = FakeNetworkOptimizer()

def monitoring_middleware(app):
    """监控中间件,用于监控请求和响应"""

    @app.before_request
    def before_request():
        """请求前处理"""
        g.start_time = time.time()
        g.client_ip = request.remote_addr

        exclude_endpoints = ['auth.login', 'auth.guest_login', 'auth.auto_guest_login', 'auth.logout', 'main.index', 'main.unified_test', 'main.combined_test', 'static']
        if request.endpoint not in exclude_endpoints:
            if network_optimizer.rate_limit_check(g.client_ip):
                logger.warning(f"IP {g.client_ip} 超过速率限制")
                return "速率限制已达上限,请稍后再试", 429

        try:
            request_data = request.get_json(silent=True) or request.form.to_dict()
            if network_optimizer.is_duplicate_request(g.client_ip, request.endpoint, request_data):
                logger.warning(f"IP {g.client_ip} 发送重复请求到 {request.endpoint}")
                return "重复请求,请稍后再试", 409
        except:
            pass

        logger.info(f"请求开始: {request.method} {request.path} - IP: {g.client_ip}")

    @app.after_request
    def after_request(response):
        """请求后处理"""
        start_time = getattr(g, 'start_time', None)
        if start_time:
            response_time = time.time() - start_time
            network_optimizer.update_performance_metrics(response_time)
            logger.info(f"请求结束: {request.method} {request.path} - 状态码: {response.status_code} - 响应时间: {response_time:.4f}s")
        else:
            response_time = 0
            logger.info(f"请求结束: {request.method} {request.path} - 状态码: {response.status_code} - 响应时间: {response_time:.4f}s")

        if response.status_code >= 400:
            error_type = "backend" if response.status_code >= 500 else "frontend"
            ai_monitor.log_error(
                error_type=error_type,
                error_message=f"请求失败: {request.method} {request.path} - 状态码: {response.status_code}",
                component="flask",
                error_stack=None
            )

        return response

    @app.errorhandler(Exception)
    def handle_exception(e):
        """异常处理"""
        response_time = time.time() - getattr(g, 'start_time', time.time())
        logger.exception(f"请求异常: {request.method} {request.path} - 异常: {str(e)}")
        ai_monitor.log_error(
            error_type="backend",
            error_message=str(e),
            error_stack=None
        )

monitoring_priority = 3
